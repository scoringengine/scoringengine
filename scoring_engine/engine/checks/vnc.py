from scoring_engine.engine.basic_check import BasicCheck


class VNCCheck(BasicCheck):
    required_properties = []
    CMD = "medusa -R 1 -h {0} -u '{1}' -p {2} -M vnc"

    def command_format(self, properties):
        account = self.get_random_account()
        username = account.username
        if account.username == 'BLANK':
            username = ' '
        return (self.get_ip_address(), username, account.password)
