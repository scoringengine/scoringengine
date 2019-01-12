from scoring_engine.engine.basic_check import BasicCheck


class HTTPOwnershipCheck(BasicCheck):
    required_properties = ['useragent', 'vhost', 'uri']
    CMD = ''

    def command_format(self, properties):
        return None
