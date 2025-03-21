from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class WinRMCheck(BasicCheck):
    required_properties = ['commands']
    CMD = CHECKS_BIN_PATH + '/winrm_check {0} {1} {2} {3}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            account.username,
            account.password,
            properties['commands']
        )
