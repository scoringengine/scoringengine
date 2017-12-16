from scoring_engine.engine.basic_check import BasicCheck


class MYSQLCheck(BasicCheck):
    required_properties = ['database', 'command']
    CMD = "mysql -h {0} -P {1} -u {2} -p{3} {4} -e {5}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.host, self.port, account.username, account.password, properties['database'], properties['command'])
