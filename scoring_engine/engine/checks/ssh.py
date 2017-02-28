from scoring_engine.engine.basic_check import BasicCheck


class SSHCheck(BasicCheck):
    required_properties = ['command']
    CMD = '/usr/bin/ssh_login {0} {1} {2} {3} {4}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.ip_address, self.port, account.username, account.password, properties['command'])
