from settings import org, api_key, N, csv_file, group_id, notify, speed, pw_mode, activate, reset_time_in_seconds, headers
import httpx
import trio
import json
from halo import Halo
from time import time


spinner = Halo(text=f'Resetting passwords', spinner='dots')
total_reset = 0
start_time = int(time())

async def get_users_in_group(send_group_users):
    async with send_group_users:
        with httpx.Client() as client:
            rel = f"/api/v1/groups/{group_id}/users?limit=200"
            r = client.get(org+rel, headers=headers)


            while r.json() != []:
                data = r.json()
                while r.status_code == 429:
                    sleep(int(r.headers['x-rate-limit-reset'] - int(time())) + 5)
                    r = client.get(org+rel, headers=headers)
                for login in data:
                    await send_group_users.send(login['id'])
                try:
                    next_link = r.headers['link'].split(",")[1].split(";")[0].replace(" ", "").replace("<", "").replace(">","")
                    r = client.get(next_link,headers=headers)
                except: break
            client.close()

            

async def reset_user_password(args):
    users = args[0]
    async with users:
        async for user in users:
            total_reset += 1
            spinner.text = f"User id {user} \t Total {total_reset} \t runtime {int((time() - start_time)/60)} minutes"
            async with httpx.AsyncClient(timeout=120) as client:
                rel = f"/api/v1/users/{user}/lifecycle/reset_password?sendEmail=true"
                r = await client.post(org+rel, headers=headers, data=json.dumps({}))

                if r.status_code == 429:
                        if reset_time_in_seconds != 0:
                            await trio.sleep(reset_time_in_seconds)
                            r = await client.post(org+rel, headers=headers, data = json.dumps({}))

                        else:
                            await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time()) + 10)
                            r = await client.post(org+rel, headers=headers, data = json.dumps({}))

                elif r.status_code == 200:
                    if speed != 100:
                        limit = int(r.headers['x-rate-limit-limit'])
                        remaining = int(r.headers['x-rate-limit-remaining'])
                        if remaining <= (limit * speed/100):
                            await trio.sleep(int(r.headers['x-rate-limit-reset']))


async def main():
    async with trio.open_nursery() as nursery:
        send_group_users, recv_channel = trio.open_memory_channel(N)
        nursery.start_soon(get_users_in_group,send_group_users)
        for i in range(0,N):
            nursery.start_soon(reset_user_password, [recv_channel.clone()])

def reset_passwords():
    spinner.info(f"Resetting passwords in group {group_id}")
    spinner.start()
    trio.run(main)
    spinner.succeed(f"Passwords reset \t group id {group_id} \t total {total_reset} \t runtime {int((time() - start_time)/60)} minutes")
