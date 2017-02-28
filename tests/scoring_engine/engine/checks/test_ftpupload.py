from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestFTPUploadCheck(CheckTest):
    check_name = 'FTPUploadCheck'
    properties = {
        'filename': 'textfile.txt',
    }
    accounts = {
        'techy': 'techypass'
    }
    cmd = "echo \"cyberengine check\" | curl -s -S -4 -v --ftp-pasv --ftp-create-dirs -T - ftp://'techy':'techypass'@'127.0.0.1'/'textfile.txt'"
