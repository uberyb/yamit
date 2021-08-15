import configparser

from halo import Halo
import httpx, json
from generate_config import generate_config

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
    confspinner.stop()
    generate_config()
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
    headers = {'Accept': 'application/json', 'Content-Type':'application/json', 'Authorization': f'SSWS {api_key}', 'X-Okta-User-Agent-Extended': 'yamit'}
    workFactor = config['PASSWORD_SETTINGS']['WORK_FACTOR']
    saltOrder = config['PASSWORD_SETTINGS']['SALT_ORDER']

confspinner.succeed("Config loaded.")
