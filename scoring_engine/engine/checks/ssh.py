from scoring_engine.engine.basic_check import BasicCheck


class SSHCheck(BasicCheck):
    required_properties = ['command']
    CMD = '/usr/bin/ssh_login {0} {1} {2} "{3}"'

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.get_ip_address(), account.username, account.password, properties['command'])
