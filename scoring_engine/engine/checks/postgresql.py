from scoring_engine.engine.basic_check import BasicCheck


class POSTGRESQLCheck(BasicCheck):
    required_properties = ['database', 'command']
    CMD = "PGPASSWORD={0} psql -h {1} -p {2} -U {3} -c {4} {5}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (account.password, self.host, self.port, account.username, properties['command'], properties['database'])
