import trio
import httpx
import csv
from settings import org, api_key, N, csv_file, group_id, notify, speed, pw_mode, activate, reset_time_in_seconds, headers
import json
from time import time
from retry import retry


start_time = time()

attributes = list()
schema_by_type = dict()
password_options =  list()
num_users = 0

    # Do data cleanup here




# filepath='users.csv'

async def csv_emitter(send_channel):
    print("All set. Beginning import.")
    async with send_channel:
        with open(csv_file, 'r', encoding='utf8') as f:
            c = csv.reader(f, delimiter=',')
            attributes = next(c)
            # attributes = c.fieldnames
            # print(attributes)
            # print(headers)
            for row in c:
                # print(row)
                await send_channel.send(row)


@retry(tries=3,delay=2)
async def worker(args):
    global num_users
    rel = args[0]
    rows = args[1]
    async with rows:
        async for row in rows:
            user_profile_complete = build_profile(row)
            async with httpx.AsyncClient(timeout=120) as client:
                try:
                    r = await client.post(org+rel, headers=headers, data = json.dumps(user_profile_complete))
                    if r.status_code == 429:
                        if reset_time_in_seconds != 0:
                            await trio.sleep(reset_time_in_seconds)
                            r = await client.post(org+rel, headers=headers, data = json.dumps(user_profile_complete))

                        else:
                            await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time()) + 10)
                            r = await client.post(org+rel, headers=headers, data = json.dumps(user_profile_complete))

                    elif r.status_code == 200:
                        if speed != 100:
                            limit = int(r.headers['x-rate-limit-limit'])
                            remaining = int(r.headers['x-rate-limit-remaining'])
                            if remaining <= (limit * speed/100):
                                await trio.sleep(int(r.headers['x-rate-limit-reset']))
                        num_users += 1
                        if num_users % notify == 0:
                            print(f"Imported {row[attributes.index('login')]} (total {num_users})")
                    else:
                        with open('log.csv', 'a',newline='') as logger:
                            w = csv.writer(logger)
                            w.writerow(['Failure', row[attributes.index('login')], r.json()['errorSummary'],r.json(), r.status_code])
                            logger.close()
                except:
                    with open('log.csv', 'a',newline='') as logger:
                            w = csv.writer(logger)
                            w.writerow(['Failure', row[attributes.index('login')], 'TIMEOUT'])
                            logger.close()
            await client.aclose()

    print("Closing worker.")


def build_credentials(row):
    global password_options
    if pw_mode == 'EMPTY':
        return None
    elif pw_mode == 'HOOK':
        c = {
            'credentials' : {
                'password' : {
                    'hook' : {
                        'type' : 'default'
                    }
                }
            }
        }
        return c
    else:
        pw_ind = password_options.index('password')
        if pw_mode == 'PLAIN':
            return {"credentials" : {"password" : {"value" : row[pw_ind]}}}
        elif pw_mode == 'BCRYPT':
            c = {
                "credentials" : {
                    "password" : {
                        "hash" : {
                            "algorithm" : pw_mode,
                            "workFactor" : config['PASSWORD_SETTINGS']['WORK_FACTOR'],
                            "salt" : row[password_options.index('salt')],
                            "value" : row[pw_ind]
                        }
                    }
                }
            }
            return c
        elif pw_mode == 'SHA-512' or pw_mode == 'SHA-256' or pw_mode == 'SHA-1' or pw_mode == 'MD5':
            c = {
                "credentials" : {
                    "password" : {
                        "hash" : {
                            "algorithm" : pw_mode,
                            "saltOrder" : config['PASSWORD_SETTINGS']['SALT_ORDER'],
                            "salt" : row[password_options.index('salt')],
                            "value" : row[pw_ind]
                        }
                    }
                }
            }
            return c
        else:
            print("Problems with password import. Please check config and csv file and try again.")
            quit()


def build_profile(row):

    prof = dict()
    for atr in attributes:
        if atr == 'password':
            pass #might need to change this back if it doesnt work
        else:
            prof[atr] = row[attributes.index(atr)].replace(" ", "")

    profile = {'profile' : prof}
    creds = build_credentials(row)
    g = {'groupIds':[group_id]}
    if creds is not None:
        return {**profile, **creds, **g}
    else: return {**profile, **g}

def check_atr():
    with httpx.Client() as client:
        r = client.get(org+'/api/v1/meta/schemas/user/default', headers=headers)
        if r.status_code == 200:
            schema = r.json()['definitions']
            schema = {**schema['base']['properties'], **schema['custom']['properties']}
            for atr in attributes:
                if atr not in schema.keys():
                    print(f"Attribute \'{atr}\' is present in csv but not added to the Okta user profile. Quitting.")
                    quit()
                else:
                    atr_type = schema[atr]['type']
                    if atr_type == 'string':
                        schema_by_type[atr] = str
                    elif atr_type == 'array':
                        schema_by_type[atr] = list
                    else:
                        schema_by_type[atr] = int
        else:
            print("Failed to retrieve Okta Org user schema, quitting.")
            quit()

async def main():
    global attributes, password_options
    with open(csv_file, 'r') as f:
        c = csv.reader(f, delimiter=',')
        print("Fetching attributes...")
        for row in c:
            attributes = row
            password_options = attributes
            if 'password' in attributes:
                pw_ind = attributes.index('password')
                attributes = attributes[:pw_ind]
            break
        f.seek(0)
        f.close()
    print("Comparing attributes to Okta user schema...")
    check_atr()
    async with trio.open_nursery() as nursery:
        send_channel, receive_channel = trio.open_memory_channel(N)
        # recv_chan = await csv_emitter('users.csv')
        nursery.start_soon(csv_emitter,send_channel)
        for i in range(0,N):
            nursery.start_soon(worker, [f'/api/v1/users?activate={activate}', receive_channel.clone()])

def import_users():
    trio.run(main)
    runtime = int(time() - start_time)
    with open('log.csv', 'a',newline='') as logger:
        w = csv.writer(logger)
        w.writerow(['Complete', f"Time in seconds: {runtime}", f"Time in minutes: {int(runtime/60)}", f"Time in hours: {int(runtime/(60**2))}"])
        logger.close()
