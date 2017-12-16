from scoring_engine.engine.basic_check import BasicCheck


class FTPDownloadCheck(BasicCheck):
    required_properties = ['filename']
    CMD = 'curl -s -S -4 -v --ftp-pasv {0}'

    def command_format(self, properties):
        account = self.get_random_account()
        url = 'ftp://' + account.username + ':' + account.password
        url += '@' + self.host + ':' + str(self.port) + properties['filename']
        return (url, '')
