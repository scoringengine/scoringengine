from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class ElasticsearchCheck(BasicCheck):
    required_properties = ['index', 'doc_type']
    CMD = CHECKS_BIN_PATH + '/elasticsearch_check {0} {1} {2} {3}'

    def command_format(self, properties):
        return (
            self.host,
            self.port,
            properties['index'],
            properties['doc_type']
        )
