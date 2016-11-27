from scoring_engine.engine.basic_check import BasicCheck
import random


class FTPDownloadCheck(BasicCheck):
    name = 'FTPDownloadCheck'
    protocol = 'ftp'
    version = 'ipv4'
    PROP_FILENAME = 'filename' 
    CMD = 'curl -s -S -4 -v --ftp-pasv ftp://{0}:{1}@{2}/{3}'

    def command(self):
        ftp_environment = self.environment
        dig_args = self.get_property_tuple(ftp_environment)
        cmd = self.CMD.format(*dig_args)
        return cmd

    def get_property_tuple(self, ftp_environment):
        account = random.choice(ftp_environment.service.accounts)
        username = account.username
        password = account.password
        ip = self.get_ip_address()
        filename = [prop.value for prop in ftp_environment.properties if prop.name == self.PROP_FILENAME][0]
        return (username, password, ip, filename)
