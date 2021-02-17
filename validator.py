import shutil
import configparser
import httpx
from time import sleep, time
import csv

config = configparser.ConfigParser()
config.read('config.ini')

csv_file = config['APP_SETTINGS']['CSV_FILE']
group_id = config['APP_SETTINGS']['GROUP_ID']
api_key = config['APP_SETTINGS']['API_TOKEN']
org = config['APP_SETTINGS']['ORG']

headers = {'Accept': 'application/json', 'Content-Type':'application/json', 'Authorization': f'SSWS {api_key}'}
found = False
target = r'failed_users.csv'

# shutil.copy(csv_file,target)
user_logins = []
ignore_logins = []
total_eval = 0
with httpx.Client() as client:
    r.client.post(org+)
    rel = f"/api/v1/groups/{group_id}/users?limit=200"
    r = client.get(org+rel, headers=headers)

    while r.json() != []:
        total_eval += len(r.json())
        print(f"Evaluated {total_eval} users.")
        data = r.json()
        while r.status_code == 429:
            sleep(int(r.headers['x-rate-limit-reset'] - int(time())) + 5)
            r = client.get(org+rel, headers=headers)
        for user in data:
            user_logins.append(user['profile']['login'])
        try:
            next_link = r.headers['link'].split(",")[1].split(";")[0].replace(" ", "").replace("<", "").replace(">","")
            r = client.get(next_link,headers=headers)
        except: break
    print(len(user_logins))
    client.close()


with open('log.csv', 'r') as l:
    cc = csv.reader(l, delimiter=",")
    for row in cc:
        if row[0] == "Failure":
            ignore_logins.append(row[1])
    l.close()



with open(csv_file, 'r',encoding='utf-8',newline='') as f:
    c = csv.reader(f, delimiter=',')
    k = 0
    for row in c:
        found = False
        for login in user_logins:
            if login == row[2] or login in ignore_logins:
                found=True
                break
        if found == False:
            k+=1
            print(f"Found a false ({k})")
            with open(target, 'a', encoding="utf-8",newline='') as ff:
                cf = csv.writer(ff, delimiter=',')
                cf.writerow(row)
                ff.close()
