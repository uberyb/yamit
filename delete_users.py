import configparser
import trio
import httpx
from time import time
from retry import retry
from settings import org, api_key, N, csv_file, group_id, notify, speed, pw_mode, activate, reset_time_in_seconds, headers


deleted_num = 0


@retry(tries=3,delay=2)
async def emit_users(args):
    deactivate_send_channel = args[0]
    rel = f"/api/v1/groups/{group_id}/users?limit=200"


    async with deactivate_send_channel:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.get(org+rel,headers=headers)
            while len(r.json()) > 0:
                try:
                    while r.status_code == 429:
                        await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time())+5)
                        r = await client.get(next_link,headers=headers)

                    for user in r.json():
                        await deactivate_send_channel.send(user['id'])

                    next_link = r.headers['link'].split(",")[1].split(";")[0].replace(" ", "").replace("<", "").replace(">","")
                    r = await client.get(next_link,headers=headers)
            # await client.aclose()

                except:
                    await client.aclose()
                    await deactivate_send_channel.aclose()
                    break
            await client.aclose()
            await deactivate_send_channel.aclose()
    print("Closing emit worker")

@retry(tries=3,delay=2)
async def deactivate_worker(args):
    deac_chan = args[0]
    delete_send_channel = args[1]
    async with deac_chan:
        async with delete_send_channel:
            async for user in deac_chan:
                async with httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(org + f'/api/v1/users/{user}/lifecycle/deactivate', headers=headers)
                    while r.status_code == 429:
                        await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time())+5)
                        r = await client.post(org + f'/api/v1/users/{user}/lifecycle/deactivate', headers=headers)
                    await delete_send_channel.send(user)

                await client.aclose()
        await delete_send_channel.aclose()
    print("Closing deactivate worker")



@retry(tries=3,delay=2)
async def delete_worker(args):
    del_chan = args[0]
    global deleted_num
    # async with del_chan:

    async with del_chan:
        async for user in del_chan:
            async with httpx.AsyncClient(timeout=120) as client:

                r = await client.delete(org + f'/api/v1/users/{user}', headers=headers)
                while r.status_code == 429:
                    await trio.sleep(int(r.headers['x-rate-limit-reset']) - int(time())+5)
                    r = await client.delete(org + f'/api/v1/users/{user}', headers=headers)
                deleted_num+=1
                if deleted_num % 100 == 0:
                    print(f"Deleted {deleted_num} users.")

            await client.aclose()
    print("Closing delete worker")

async def main():
    async with trio.open_nursery() as nursery:
        deactivate_send_channel, deactivate_receive_channel = trio.open_memory_channel(0)
        delete_send_channel, delete_receive_channel = trio.open_memory_channel(0)
        nursery.start_soon(emit_users, [deactivate_send_channel])
        for i in range(5):
            nursery.start_soon(deactivate_worker,[deactivate_receive_channel.clone(),delete_send_channel.clone()])
        for i in range(5):
            nursery.start_soon(delete_worker,[delete_receive_channel.clone()])
        # print(nursery.child_tasks)


def delete_users():
    trio.run(main)
