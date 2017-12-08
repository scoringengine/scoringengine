from scoring_engine.engine.basic_check import BasicCheck


class SSHCheck(BasicCheck):
    required_properties = ['command']
    CMD = 'sshpass -p {0} ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {1} -p {2} {3}'

    def command_format(self, properties):
        account = self.get_random_account()
        username_domain = account.username + '@' + self.host
        return (account.password, username_domain, self.port, properties['command'])
