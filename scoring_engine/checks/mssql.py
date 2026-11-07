from scoring_engine.engine.basic_check import BasicCheck


class MSSQLCheck(BasicCheck):
    REQUIRES_PACK = "db"
    required_properties = ["database", "command"]
    CMD = "SQLCMDPASSWORD={3} sqlcmd -S {0},{1} -U {2} -d {4} -Q {5}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.host, self.port, account.username, self.secret(account.password), properties["database"], properties["command"])
