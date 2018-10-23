from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class SMTPCheck(BasicCheck):
    required_properties = ['touser', 'subject', 'body']
    CMD = CHECKS_BIN_PATH + '/smtp_check {0} {1} {2} {3} {4} {5} {6} {7}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            account.username,
            account.password,
            account.username,
            properties['touser'],
            properties['subject'],
            properties['body'],
            self.host,
            self.port
        )
