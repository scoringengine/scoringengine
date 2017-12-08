from scoring_engine.engine.basic_check import BasicCheck


class FTPCheck(BasicCheck):
    CMD = "medusa -R 1 -h {0} -n {1} -u {2} -p {3} -M ftp"

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.host, self.port, account.username, account.password)
