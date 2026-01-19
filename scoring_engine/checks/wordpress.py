from scoring_engine.engine.http_post_check import HTTPPostCheck


class WordpressCheck(HTTPPostCheck):
    required_properties = ['useragent', 'vhost', 'uri']
    CMD = 'curl -s -S -4 -v -L --cookie-jar - --header {0} -A {1} --data {2} {3}'

    def command_format(self, properties):
        account = self.get_random_account()
        host_header = 'Host: ' + properties['vhost']
        data = 'log=' + account.username + '&pwd=' + account.password
        uri = self.host + ':' + str(self.port) + properties['uri']
        return (host_header, properties['useragent'], data, uri)
