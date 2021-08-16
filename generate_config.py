from pathlib import Path
import sys

def generate_config():
    config_file = Path("config.ini")
    if config_file.is_file():
        print("\033[1m\033[91mConfig file exists already. Please delete it and rerun.")
    else:
        max_concurrent_sessions = input("\033[1mHow many concurrent http sessions would you like? (default 20, also need an integer between 1 and 20): ")
        if max_concurrent_sessions is None:
            max_concurrent_sessions = 20
        try:
            int(max_concurrent_sessions)
        except ValueError:
            print("\033[91mOnly integers are allowed, sorry.")
            sys.exit(1)
        if int(max_concurrent_sessions) > 20 or int(max_concurrent_sessions) < 1:
            print("\033[91mBad value.")
            sys.exit(1)
        
        org_url = input("\033[1mEnter your full Okta org url (https://subdomain.okta.com): ")
        api_token = input("\033[1mEnter your API token (super admin permissions required): ")
        csv_file = input("\033[1mEnter the name of your csv file (default users.csv): ")
        group_id = input("\033[1mEnter a custom group id to import users into. An empty value will create a group for you: ")
        speed = input("\033[1mEnter the percentage of your rate limit you would like to consume (default 95): ")
        activate = input("\033[1mWould you like to activate users? (y/n): ")
        password_type = input("\033[1mPassword type? (EMPTY, PLAIN, HOOK, BCRYPT, SHA-512, SHA-256, SHA-1, MD5): ")
        salt_order = input("\033[1mSalt order? (Leave empty if unsure): ")
        work_factor = input("\033[1mWork factor? (Leave empty unless using BCRYPT): ")
        with open("config.ini", 'a') as f:
            f.write("[APP_SETTINGS]\n")
            f.write(f"MAX_CONCURRENT_SESSIONS = {str(max_concurrent_sessions)}\n")

            f.write(f"ORG = {org_url}\n")
            f.write(f"API_TOKEN = {api_token}\n")
            if csv_file == "":
                csv_file = "users.csv"
            f.write(f"CSV_FILE = {csv_file}\n")
            if group_id == "":
                f.write(f"GROUP_ID = \n")
            f.write("NOTIFY = 1\n")
            if speed == "":
                speed = "95"
            if int(speed) > 100 or int(speed) < 1:
                print("Bad speed value.")
                sys.exit(1)
            f.write(f"SPEED = {speed}\n")
            if activate == 'y':
                activate = "true"
            else:
                activate = "false"
            f.write(f"ACTIVATE = {activate}\n\n")

            f.write(f"[PASSWORD_SETTINGS]\n")
            f.write(f"PASSWORD_TYPE = {password_type}\n")
            if salt_order == "":
                f.write(f"SALT_ORDER = \n")
            else:
                f.write(f"SALT_ORDER = {salt_order}\n")
            if work_factor == "":
                f.write(f"WORK_FACTOR = \n")
            else:
                f.write(f"WORK_FACTOR = {work_factor}\n")

            f.write("\n[ADVANCED]\nRESET_TIME_IN_SECONDS = 0")
            print("\033[1mGenerated config file.")
            f.close()