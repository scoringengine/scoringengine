from scoring_engine.engine.username_password_check import UsernamePasswordCheck


class SSHCheck(UsernamePasswordCheck):
    name = "SSH IPv4 Check"
    protocol = 'ssh'
    version = 'ipv4'

    def command(self):
        return 'ssh command here'
