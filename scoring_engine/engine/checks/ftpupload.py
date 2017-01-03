from scoring_engine.engine.basic_check import BasicCheck
import random


class FTPUploadCheck(BasicCheck):
    PROP_FILENAME = 'filename'
    CMD = 'echo "cyberengine check" | curl -s -S -4 -v --ftp-pasv --ftp-create-dirs -T - ftp://{0}:{1}@{2}/{3}'

    def command(self):
        ftp_environment = self.environment
        dig_args = self.get_property_tuple(ftp_environment)
        cmd = self.CMD.format(*dig_args)
        return cmd

    def get_property_tuple(self, ftp_environment):
        account = random.choice(self.environment.service.accounts)
        username = account.username
        password = account.password
        ip = self.get_ip_address()
        filename = self.get_property_by_name(self.PROP_FILENAME)
        return (username, password, ip, filename)
