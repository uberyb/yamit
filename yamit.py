import argparse



 







if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--delete-users',action='store_true')
    parser.add_argument('-x', '--no-import', action='store_false')
    parser.add_argument('-r', '--reset-passwords', action='store_true')
    parser.add_argument('-i', '--information', action='store_true')
    parser.add_argument('-c', '--gen-config', action='store_true')
    args = parser.parse_args()
    


    if args.gen_config:
        from generate_config import generate_config
        generate_config()
        
    from settings import *
    if args.information:
        from information import information
        information()
    if args.delete_users:   
        from delete_users import delete_users 
        delete_users()
    if args.no_import and not args.delete_users and not args.information and not args.reset_passwords and not args.gen_config:
        from import_users import import_users
        import_users()
    if args.reset_passwords:
        from passwords import reset_passwords
        reset_passwords()
    
        