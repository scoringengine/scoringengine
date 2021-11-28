from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class FTPCheck(BasicCheck):
    required_properties = ["remotefilepath", "filecontents"]
    CMD = CHECKS_BIN_PATH + "/ftp_check {0} {1} {2} {3} {4} {5}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties["remotefilepath"],
            properties["filecontents"],
        )
