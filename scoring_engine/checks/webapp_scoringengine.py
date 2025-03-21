from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class WebappScoringengineCheck(BasicCheck):
    required_properties = ['scheme', 'basepath']
    CMD = 'pytest --tb=line -s -q -rA --scheme={0} --hostip={1} --hostport={2} --basepath={3} --username={4} --password={5} ' + CHECKS_BIN_PATH + '/webapp_scoringengine_check.py'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            properties['scheme'],
            self.host,
            self.port,
            properties['basepath'],
            account.username,
            account.password
        )
