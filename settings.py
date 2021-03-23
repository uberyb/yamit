import configparser

from halo import Halo
import httpx, json

confspinner = Halo(text=f'Starting yamit.', spinner='dots')
confspinner.start()
org, api_key, N, csv_file, group_id, notify, speed, pw_mode, activate, reset_time_in_seconds = ("" for i in range(10))
attributes = list()
schema_by_type = dict()
password_options =  list()
num_users = 0

confspinner.text = "Loading config..."
config = configparser.ConfigParser()

config.read('config.ini')

if len(config.sections()) == 0:
    print("Config file not found. Please make sure there is a config.ini file in the same directory as app.py.")
    quit()
else:
    org = config['APP_SETTINGS']['ORG']
    if not org.startswith('https://'):
        org = "https://" + org
    if org[-1] == "/":
        org = org[:len(org)-1]
    N = int(config['APP_SETTINGS']['MAX_CONCURRENT_SESSIONS'])
    api_key = config['APP_SETTINGS']['API_TOKEN']
    csv_file = config['APP_SETTINGS']['CSV_FILE']
    group_id = config['APP_SETTINGS']['GROUP_ID']
    notify = int(config['APP_SETTINGS']['NOTIFY'])
    speed = int(config['APP_SETTINGS']['SPEED'])
    pw_mode = config['PASSWORD_SETTINGS']['PASSWORD_TYPE']
    activate = config['APP_SETTINGS']['ACTIVATE'].lower()
    reset_time_in_seconds = int(config['ADVANCED']['RESET_TIME_IN_SECONDS'])
    headers = {'Accept': 'application/json', 'Content-Type':'application/json', 'Authorization': f'SSWS {api_key}'}
    workFactor = config['PASSWORD_SETTINGS']['WORK_FACTOR']
    saltOrder = config['PASSWORD_SETTINGS']['SALT_ORDER']

    if group_id == "":
        data = {"profile": {"name":"yamit Imported Users", "description":"Group to place yamit imported users into if GROUP_ID was left blank."}}
        r = httpx.post(url+'/api/v1/groups', headers = headers, data = json.dumps(data))
        try:
            group_id = r.json()['id']
        except Exception as e:
            confspinner.info(f"Exception {e}")

confspinner.succeed("Config loaded.")