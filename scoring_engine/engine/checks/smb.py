from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class SMBCheck(BasicCheck):
    required_properties = ['commands']
    CMD = CHECKS_BIN_PATH + '/smb_check.py --host {0} --user {1} --pass {2} --share {3} --file {4} --hash {5}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            account.username,
            account.password,
            properties['share'],
            properties['file'],
            properties['hash']
        )
