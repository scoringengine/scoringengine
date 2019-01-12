from scoring_engine.engine.basic_check import BasicCheck


class HTTPOwnershipCheck(BasicCheck):
    """
    An HTTP check for King of the Hill competitions that is used to determine
    which team has ownership over the service.
    """
    # Same required properties for a normal HTTP check
    required_properties = ['useragent', 'vhost', 'uri']
    # A separate script is used in order to process the response and find the
    # ownership hash
    CMD = '/http_ownership_check {0} {1} {2} {3} {4}'

    def command_format(self, properties):
        return (
            self.host,
            self.port,
            properties['useragent'],
            properties['vhost'],
            properties['uri'],
        )
