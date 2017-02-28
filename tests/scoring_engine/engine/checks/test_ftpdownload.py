from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestFTPDownloadCheck(CheckTest):
    check_name = 'FTPDownloadCheck'
    properties = {
        'filename': '/textfile.txt',
    }
    accounts = {
        'techy': 'techypass'
    }
    cmd = "curl -s -S -4 -v --ftp-pasv 'ftp://techy:techypass@127.0.0.1:100/textfile.txt'"
