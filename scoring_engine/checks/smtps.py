from scoring_engine.engine.basic_check import BasicCheck


class SMTPSCheck(BasicCheck):
    required_properties = ['fromuser', 'touser', 'subject', 'body']
    CMD = 'smtps_check {0} {1} {2} {3} {4} {5} {6} {7}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            account.username,
            account.password,
            properties['fromuser'],
            properties['touser'],
            properties['subject'],
            properties['body'],
            self.host,
            self.port
        )
