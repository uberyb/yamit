import trio
import httpx
import csv
from settings import org, api_key, N, csv_file, group_id, notify, speed, pw_mode, activate, reset_time_in_seconds, headers, workFactor, saltOrder
import json
from time import time
from retry import retry

from halo import Halo

start_time = time()

attributes = list()
schema_by_type = dict()
password_options =  list()
num_users = 0

spinner = Halo(text=f'Importing...', spinner='dots')


async def csv_emitter(send_channel):
    global spinner
    spinner.text = "All set. Beginning import."
    async with send_channel:
        with open(csv_file, 'r', encoding='utf8') as f:
            c = csv.reader(f, delimiter=',')
            attributes = next(c)
            for row in c:
                await send_channel.send(row)


@retry(tries=3,delay=2)
async def worker(args):
    global num_users, spinner
    rel = args[0]
    rows = args[1]
    global start_time
    async with rows:
        async for row in rows:
            user_profile_complete = build_profile(row)
            async with httpx.AsyncClient(timeout=120) as client:
                # try:
                r = await client.post(org+rel, headers=headers, data = json.dumps(user_profile_complete))
                while r.status_code == 429:
                    if reset_time_in_seconds != 0:
                        await trio.sleep(reset_time_in_seconds)
                        # r = await client.post(org+rel, headers=headers, data = json.dumps(user_profile_complete))

                    else:
                        await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time()) + 10)

                    r = await client.post(org+rel, headers=headers, data = json.dumps(user_profile_complete))


    
                num_users += 1
                # print(f"Rem: {r.headers['x-rate-limit-remaining']} \t No: {num_users}")
                if num_users % notify == 0:
                    # print("notify")
                    # print(f"Last imported {row[attributes.index('login')]} \t total {num_users} \t remaining-api-calls {r.headers['x-rate-limit-remaining']} \t status {r.status_code}")
                    spinner.text = f"Last imported {row[attributes.index('login')]} \t total {num_users} \t runtime {int(int(time() - start_time)/60)} minutes \t status {r.status_code}"
                

                if speed != 100:
                    limit = int(r.headers['x-rate-limit-limit'])
                    remaining = int(r.headers['x-rate-limit-remaining'])
                    if (remaining <= (limit+N - (limit * speed/100))) and (int(r.headers['x-rate-limit-reset']) - int(time())) > 0:
                        # spinner.info(f"Waiting for {int(r.headers['x-rate-limit-reset']) - int(time())} seconds to avoid being rate limited.")
                        await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time()))
                        # spinner.start()
                    
                    
                if r.status_code != 200 and r.status_code != 429:
                    with open('log.csv', 'a',newline='') as logger:
                        w = csv.writer(logger)
                        w.writerow(['Failure', row[attributes.index('login')], r.json()['errorSummary'], r.status_code])
                        logger.close()
                # except:
                #     with open('log.csv', 'a',newline='') as logger:
                #             w = csv.writer(logger)
                #             w.writerow(['Failure', row[attributes.index('login')], 'TIMEOUT'])
                #             logger.close()
            # await client.aclose()

    # print("Closing worker.")
    


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
                            "workFactor" : workFactor,
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
                            "saltOrder" : saltOrder,
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
    global group_id
    if group_id == "":
        confspinner.info("No group id specified. Creating yamit group...")
        data = {"profile": {"name":"yamit Imported Users", "description":"Group to place yamit imported users into if GROUP_ID was left blank."}}
        r = httpx.post(org+'/api/v1/groups', headers = headers, data = json.dumps(data))
        try:
            group_id = r.json()['id']
            confspinner.succeed(f"Group created with id {group_id}")
            confspinner.start()
        except Exception as e:
            confspinner.info(f"Exception {e}")

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
    global attributes, password_options, spinner
    mainspinner = Halo(text='yamit Importing ', spinner='dots')
    mainspinner.start()
    with open(csv_file, 'r') as f:
        c = csv.reader(f, delimiter=',')
        mainspinner.succeed("Fetching attributes...")
        mainspinner.start()
        for row in c:
            attributes = row
            password_options = attributes
            if 'password' in attributes:
                pw_ind = attributes.index('password')
                attributes = attributes[:pw_ind]
            break
        f.seek(0)
        f.close()
    
    check_atr()
    mainspinner.succeed("Compared attributes to Okta user schema...")
    async with trio.open_nursery() as nursery:
        send_channel, receive_channel = trio.open_memory_channel(0)
        # recv_chan = await csv_emitter('users.csv')
        nursery.start_soon(csv_emitter,send_channel)
        
        spinner.start()
        for i in range(0,N):
            nursery.start_soon(worker, [f'/api/v1/users?activate={activate}', receive_channel.clone()])



def import_users():
    global spinner
    trio.run(main)
    
    runtime = int(time() - start_time)
    with open('log.csv', 'a',newline='') as logger:
        w = csv.writer(logger)
        w.writerow(['Complete', f"Time in seconds: {runtime}", f"Time in minutes: {int(runtime/60)}", f"Time in hours: {int(runtime/(60**2))}"])
        spinner.succeed(f"Complete! \t time (sec) {runtime} \t time (min) {int(runtime/60)} \t time (hour) {int(runtime/(60**2))}")
        logger.close()
