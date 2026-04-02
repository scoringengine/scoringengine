from scoring_engine.engine.basic_check import CHECKS_BIN_PATH, BasicCheck


class WinRMCheck(BasicCheck):
    required_properties = ["commands"]
    CMD = CHECKS_BIN_PATH + "/winrm_check {0} {1} {2} {3} {4} {5}"

    def command_format(self, properties):
        account = self.get_random_account()
        show_command = properties.get("show_command", "false")
        return (self.host, self.port, account.username, account.password, properties["commands"], show_command)
