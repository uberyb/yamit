import argparse
from settings import *
from import_users import import_users
from delete_users import delete_users
from passwords import reset_passwords 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--delete-users',action='store_true')
    parser.add_argument('-x', '--no-import', action='store_false')
    parser.add_argument('-r', '--reset-passwords', action='store_true')
    args = parser.parse_args()
    


    if args.delete_users:
        delete_users()
    if args.no_import and not args.delete_users:
        import_users()
    if args.reset_passwords:
        reset_passwords()
        