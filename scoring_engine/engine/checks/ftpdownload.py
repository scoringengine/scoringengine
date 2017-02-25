from scoring_engine.engine.basic_check import BasicCheck


class FTPDownloadCheck(BasicCheck):
    required_properties = ['filename']
    CMD = 'curl -s -S -4 -v --ftp-pasv ftp://{0}:{1}@{2}/{3}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (account.username, account.password, self.get_ip_address(), self.properties['filename'])
