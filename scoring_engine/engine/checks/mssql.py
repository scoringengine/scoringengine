from scoring_engine.engine.basic_check import BasicCheck


class MSSQLCheck(BasicCheck):
    required_properties = ['database', 'command']
    CMD = "/opt/mssql-tools/bin/sqlcmd -S {0},{1} -U {2} -P {3} -d {4} -Q {5}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.host, self.port, account.username, account.password, properties['database'], properties['command'])
