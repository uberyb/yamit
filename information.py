from settings import org, api_key, N, csv_file, group_id, notify, speed, pw_mode, activate, reset_time_in_seconds, headers, workFactor, saltOrder
import httpx
from halo import Halo
import csv

def csv_count(csv_file):
    num = 0
    try:
        with open(csv_file, 'r', encoding='utf8') as f:
            c = csv.reader(f, delimiter=',')
            attributes = next(c)
            for row in c:
                num +=1
    except Exception as e:
        print(e)
        
    return num

def rate_limit(headers,org):
    r = httpx.post(org + '/api/v1/users/me', headers=headers)
    return r.headers.get('x-rate-limit-limit')

def information():
    spinner = Halo(text=f'Loading users CSV...', spinner='dots')
    count = csv_count(csv_file)
    spinner.succeed("Loaded.")
    spinner.start()
    spinner.text = "Getting rate limit for POST to /users"
    lim = rate_limit(headers,org)
    spinner.info(f"Rate limit is {lim} per minute.")
    spinner.start()
    spinner.info(f"yamit should take {int(count/((speed/100)*int(lim)))} minutes to complete under your current settings.")

