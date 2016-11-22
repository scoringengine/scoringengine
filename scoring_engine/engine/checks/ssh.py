from scoring_engine.engine.basic_check import BasicCheck


class SSHCheck(BasicCheck):
    name = "SSH IPv4 Check"
    protocol = 'ssh'
    version = 'ipv4'

    def command(self):
        return 'ssh command here'
