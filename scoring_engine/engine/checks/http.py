from scoring_engine.engine.basic_check import BasicCheck


class HTTPCheck(BasicCheck):
    required_properties = ['useragent', 'vhost', 'uri']
    CMD = 'curl -s -S -4 -v -L -A {0} {1}'

    def command_format(self, properties):
        url = 'http://' + properties['vhost'] + ':' + str(self.port) + properties['uri']
        return (properties['useragent'], url)
