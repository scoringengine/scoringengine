#!/usr/bin/env python

# A scoring engine check that logs into FTP, uploads a file
# and then logs into FTP again, and downloads the file

import sys
import ftplib
import tempfile
import os

if len(sys.argv) != 7:
    print("Usage: " + sys.argv[0] + " host port username password remotefilepath filecontents")
    sys.exit(1)

host = sys.argv[1]
port = sys.argv[2]
username = sys.argv[3]
password = sys.argv[4]
remote_filepath = sys.argv[5]
upload_file_contents = sys.argv[6]

# Connect and Upload file to server
session = ftplib.FTP()
session.connect(host=host, port=int(port))
session.login(username, password)
tmp_fd, tmp_filename = tempfile.mkstemp(text=True)
with open(tmp_filename, 'w') as fobj:
    fobj.write(upload_file_contents)
upload_response_text = session.storlines('STOR {0}'.format(remote_filepath), open(tmp_filename, 'rb'))
session.quit()
session.close()
os.remove(tmp_filename)

# Success code is 226
if not upload_response_text.startswith('226'):
    print("ERROR: Unable to upload file")
    print(upload_response_text)
    sys.exit(1)

# Connect and Download file
session = ftplib.FTP()
session.connect(host=host, port=int(port))
session.login(username, password)
downloaded_lines = []
download_response_text = session.retrlines('RETR {0}'.format(remote_filepath), downloaded_lines.append)
session.quit()
session.close()

# Success code is 226
if not download_response_text.startswith('226'):
    print("ERROR: Unable to download file")
    print(download_response_text)
    sys.exit(1)

downloaded_data = ''.join(downloaded_lines)
if downloaded_data != upload_file_contents:
    print("ERROR: Uploaded contents do not match downloaded contents")
    sys.exit(1)

print("SUCCESS")
print(downloaded_data)
