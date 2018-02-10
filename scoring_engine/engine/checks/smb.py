from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class SMBCheck(BasicCheck):
    required_properties = ['share', 'file', 'hash']

    CMD = CHECKS_BIN_PATH + '/smb_check --host {0} --port {1} --user {2} --pass {3} --share {4} --file {5} --hash {6}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties['share'],
            properties['file'],
            properties['hash']
        )
