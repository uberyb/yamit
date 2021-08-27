from settings import org, api_key, N, csv_file, group_id, notify, speed, pw_mode, activate, reset_time_in_seconds, headers, workFactor, saltOrder
import httpx
import pandas as pd


# df.column_name != whole string from the cell
# now, all the rows with the column: Name and Value: "dog" will be deleted




def validate_users():
    url = '/api/v1/groups/' + group_id + '/users?limit=200'
    r = httpx.get(org + url, headers=headers)
    df = pd.read_csv(csv_file)
    final = False
    while 'next' in r.links or final:
        for user in r.json():
            df = df[df.login != user['profile']['login']]
        if not final:
            r = httpx.get(r.links['next']['url'], headers=headers)
            if 'next' not in r.links:
                final = True
        else: final = False


    df.to_csv("errored_users.csv", index=False)
