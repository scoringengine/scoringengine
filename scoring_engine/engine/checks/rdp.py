from scoring_engine.engine.basic_check import BasicCheck


class RDPCheck(BasicCheck):
    required_properties = []

    CMD = 'xfreerdp --ignore-certificate --authonly -u {0} -p {1} {2}:{3}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            account.username,
            account.password,
            self.host,
            self.port,
        )
