from scoring_engine.engine.basic_check import CHECKS_BIN_PATH, BasicCheck


class RDPCheck(BasicCheck):
    required_properties = []
    CMD = CHECKS_BIN_PATH + "/rdp_check {0} {1} {2} {3}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            account.username,
            account.password,
            self.host,
            self.port,
        )
