from scoring_engine.engine.basic_check import BasicCheck


class SSHCheck(BasicCheck):
    required_properties = ['command']
    CMD = 'expect -c "spawn ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}@{1} \'{2}\'; expect \'assword\'; send \'{3}\r\'; interact\''

    def command_format(self, properties):
        account = self.get_random_account()
        return (account.username, self.get_ip_address(), properties['command'], account.password)
