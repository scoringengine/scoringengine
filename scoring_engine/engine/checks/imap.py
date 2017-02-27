from scoring_engine.engine.basic_check import BasicCheck


class IMAPCheck(BasicCheck):
    required_properties = ['domain']
    CMD = "medusa -R 1 -h {0} -u {1}@{2} -p {3} -M imap -m AUTH:LOGIN"

    def command_format(self, properties):
        account = self.get_random_account()
        return (self.get_ip_address(), account.username, properties['domain'], account.password)
