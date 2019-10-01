from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class TelnetCheck(BasicCheck):
    required_properties = ['timeout', 'commands']
    CMD = CHECKS_BIN_PATH + '/telnet_check {0} {1} {2} {3} {4} {5}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            properties['timeout'],
            account.username,
            account.password,
            properties['commands']
        )
