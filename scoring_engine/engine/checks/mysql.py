from scoring_engine.engine.basic_check import BasicCheck


class MYSQLCheck(BasicCheck):
    required_properties = ['database', 'command']
    CMD = "mysql -h {0} -u {1} -p{2} {3} -e '{4}'"

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.get_ip_address(), account.username, account.password, properties['database'], properties['command'])
