"""
Example service configuration:
- name: KOTH-HTTP
  check_name: HTTPCheck
  host: testbed_koth_http
  port: 80
  points: 25
  environments:
  - matching_content: "^[A-F0-9a-f]{6}$"  # Regex to match RGB hex string
    properties:
    - name: useragent
      value: Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)
    - name: vhost
      value: testbed_koth_web
    - name: uri
      value: "/ownership.html"
"""
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
