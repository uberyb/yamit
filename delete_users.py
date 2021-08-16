import configparser
import trio
import httpx
from time import time
# from retry import retry
from settings import org, api_key, N, csv_file, group_id, notify, speed, pw_mode, activate, reset_time_in_seconds, headers
import math

from halo import Halo


start_time = int(time())
spinner = Halo(text=f'Deleting users...', spinner='dots')
deleted_num = 0

async def emit_users(args):
    deactivate_send_channel = args[0]
    rel = f"/api/v1/groups/{group_id}/users?limit=200"

    async with deactivate_send_channel:
        async with httpx.AsyncClient(timeout=120) as client:
            job_finished = False
            r = await client.get(org+rel,headers=headers)
            while not job_finished:
            
                while r.status_code == 429:
                    await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time())+5)
                    r = await client.get(next_link,headers=headers)
            
                if r.status_code == 200:
                    for user in r.json():
                        await deactivate_send_channel.send(user['id'])
                    if hasattr(r, 'links'):
                        
                        next = r.links.get('next')
                        if next:
                            r = await client.get(next['url'], headers=headers)
                        else: job_finished = True

async def deactivate_worker(args):
    deac_chan = args[0]
    delete_send_channel = args[1]
    global deleted_num, spinner
    async with delete_send_channel:
        
        async with deac_chan:
            async for user in deac_chan:
                
                
                async with httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(org + f'/api/v1/users/{user}/lifecycle/deactivate', headers=headers)
                    while r.status_code == 429:
                        
                        await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time())+5)
                        r = await client.post(org + f'/api/v1/users/{user}/lifecycle/deactivate', headers=headers)

                    r = await client.delete(org + f'/api/v1/users/{user}', headers=headers)
                    while r.status_code == 429:
                        # spinner.info(f"Sleeping for {int(r.headers['x-rate-limit-reset']) - int(time())+5} seconds...")
                        await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time())+5)
                        # spinner.start()
                        r = await client.delete(org + f'/api/v1/users/{user}', headers=headers)
                    deleted_num+=1
                    if deleted_num % notify == 0:
                        spinner.text = f"Deleted {deleted_num} users \t runtime {int(time()) - start_time} seconds"



                
async def main():
    global spinner
    spinner.start()
    async with trio.open_nursery() as nursery:
        deactivate_send_channel, deactivate_receive_channel = trio.open_memory_channel(0)
        delete_send_channel, delete_receive_channel = trio.open_memory_channel(0)
        nursery.start_soon(emit_users, [deactivate_send_channel])
        for i in range(N):
            nursery.start_soon(deactivate_worker,[deactivate_receive_channel.clone(),delete_send_channel.clone()])

def delete_users():
    global spinner
    spinner.text = f"Deleting users from {group_id}"
    trio.run(main)
    spinner.succeed("Completed.")
