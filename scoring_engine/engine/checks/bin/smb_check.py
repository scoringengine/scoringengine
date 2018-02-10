#!/usr/bin/env python
import tempfile
import argparse
from smb.SMBConnection import SMBConnection
import hashlib

def check_smb(host, share_name, file_name, username, password, hash_to_test):
    try:
        conn = SMBConnection(username, password, 'name', 'lets_see_if_this_matters',
                             use_ntlm_v2=True, is_direct_tcp=True)
        conn.connect(host, 445)
        shares = conn.listShares()

        for share in shares:
            if share.name.strip() == share_name:
                with tempfile.NamedTemporaryFile() as temp_file:
                    test = conn.retrieveFile(share.name, '/{}'.format(file_name), temp_file)
                    temp_file.seek(0)
                    data = temp_file.read()
                    hash_obj = hashlib.sha256(data)
                    if hash_obj.hexdigest() == hash_to_test:
                        print('SUCCESS')
                        return
    except Exception as e:
        print(str(e))
    print('Failed check')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='ip to test', dest='host')
    parser.add_argument('--user', help='username', dest='user')
    parser.add_argument('--pass', help='password', dest='passw')
    parser.add_argument('--share', help='share name', dest='share')
    parser.add_argument('--file', help='file name', dest='file')
    parser.add_argument('--hash', help='hash for comparison of file to endpoint', dest='hash')
    args = parser.parse_args()
    check_smb(args.host, args.share, args.file, args.user, args.passw, args.hash)

if __name__ == '__main__':
    main()
