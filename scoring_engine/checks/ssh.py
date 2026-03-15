from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class SSHCheck(BasicCheck):
    required_properties = ['commands']
    CMD = CHECKS_BIN_PATH + '/ssh_check {0} {1} {2} {3}'

    def command_format(self, properties):
        account = self.get_random_account()
        self._current_account = account
        return (
            self.host,
            self.port,
            account.username,
            properties['commands']
        )

    def command_env(self):
        if hasattr(self, '_current_account'):
            return {'SCORING_PASSWORD': self._current_account.password}
        return {}
