from scoring_engine.engine.basic_check import CHECKS_BIN_PATH, BasicCheck


class OpenVPNCheck(BasicCheck):
    required_properties = ["ca"]
    CMD = CHECKS_BIN_PATH + "/openvpn_check {0} {1} {2} {3} {4}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.host, self.port, account.username, account.password, properties["ca"])
