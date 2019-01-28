from scoring_engine.engine.basic_check import BasicCheck


class WordpressCheck(BasicCheck):
    required_properties = ['useragent', 'vhost', 'data', 'uri']
    CMD = 'curl -s -S -4 -v -L --cookie-jar - --header {0} -A {1} --data {2} {3}'

    def command_format(self, properties):
        host_header = 'Host: ' + properties['vhost']
        host_uri = self.host + ':' + str(self.port) + properties['uri']
        return host_header, properties['useragent'], properties['data'], host_uri
