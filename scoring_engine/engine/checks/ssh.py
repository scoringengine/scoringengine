from scoring_engine.engine.basic_check import BasicCheck


class SSHCheck(BasicCheck):

    def command(self):
        return 'ssh command here'
