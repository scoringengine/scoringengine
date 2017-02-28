from scoring_engine.engine.basic_check import BasicCheck


class POSTGRESQLCheck(BasicCheck):
    required_properties = ['database', 'command']
    CMD = "PGPASSWORD={0} psql -h {1} -U {2} -c {3} {4}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (account.password, self.get_ip_address(), account.username, properties['command'], properties['database'])
