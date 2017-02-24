from scoring_engine.engine.basic_check import BasicCheck


class HTTPCheck(BasicCheck):
    required_properties = ['useragent', 'uri']
    CMD = 'curl -s -S -4 -v -L  -A "{0}" http://{1}{2}'

    def command_format(self, properties):
        return (properties['useragent'], self.get_ip_address(), properties['uri'])
