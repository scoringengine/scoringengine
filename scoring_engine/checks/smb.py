from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class SMBCheck(BasicCheck):
    required_properties = ['remote_name', 'share', 'file', 'hash']
    CMD = CHECKS_BIN_PATH + '/smb_check --host {0} --port {1} --user {2} --pass {3} ' \
                            '--remote-name {4} --share {5} --file {6} --hash {7}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties['remote_name'],
            properties['share'],
            properties['file'],
            properties['hash']
        )
