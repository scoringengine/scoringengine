from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class WebappNginxdefaultpageCheck(BasicCheck):
    required_properties = ['scheme', 'basepath']
    CMD = 'pytest --tb=line -s -q -rA --scheme={0} --hostip={1} --hostport={2} --basepath={3} ' + CHECKS_BIN_PATH + '/webapp_nginxdefaultpage_check.py'

    def command_format(self, properties):
        return (
            properties['scheme'],
            self.host,
            self.port,
            properties['basepath']
        )
