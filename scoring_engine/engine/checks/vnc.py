from scoring_engine.engine.basic_check import BasicCheck


class VNCCheck(BasicCheck):
    required_properties = []
    CMD = "medusa -R 1 -h {0} -n {1} -u '{2}' -p {3} -M vnc"

    def command_format(self, properties):
        account = self.get_random_account()
        username = account.username
        if account.username == 'BLANK':
            username = ' '
        return (self.host, self.port, username, account.password)
