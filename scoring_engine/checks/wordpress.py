from scoring_engine.engine.http_post_check import HTTPPostCheck


class WordpressCheck(HTTPPostCheck):
    required_properties = ['useragent', 'vhost', 'uri']
    CMD = 'curl -s -S -4 -v -L --cookie-jar - --header \'Host: {0}\' -A \'{1}\' --data \'log={2}&pwd={3}\' \'{4}:{5}{6}\''

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            properties['vhost'],
            properties['useragent'],
            account.username,
            account.password,
            self.host,
            self.port,
            properties['uri']
        )
