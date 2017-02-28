from scoring_engine.engine.basic_check import BasicCheck


class HTTPSCheck(BasicCheck):
    required_properties = ['useragent', 'vhost', 'uri']
    CMD = 'curl -s -S -4 -v -L -k --ssl-reqd -A {0} {1}'

    def command_format(self, properties):
        url = 'https://' + properties['vhost'] + ':' + str(self.port) + properties['uri']
        return (properties['useragent'], url)
