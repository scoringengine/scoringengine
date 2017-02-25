from scoring_engine.engine.basic_check import BasicCheck


class HTTPSCheck(BasicCheck):
    required_properties = ['useragent', 'vhost', 'uri']
    CMD = 'curl -s -S -4 -v -L -k --ssl-reqd -A "{0}" https://{1}{2}'

    def command_format(self, properties):
        return (properties['useragent'], properties['vhost'], properties['uri'])
