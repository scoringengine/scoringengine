"""
Example service configuration:
- name: KOTH-Telnet
  check_name: TelnetOwnershipCheck
  host: testbed_koth_telnet
  port: 23
  points: 25
  accounts:
  - username: ttesterson
    password: testpass
  environments:
  - matching_content: "^SUCCESS"
    properties:
    - name: commands
      value: id; ls -l /home
    - name: ownershipfilepath
"""
from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class TelnetOwnershipCheck(BasicCheck):
    """
    A Telnet check for King of the Hill competitions that is used to determine
    which team has ownership over the service by parsing an ownership file for
    an ownership hash.
    """
    # We need to know where to find the ownership file
    required_properties = ['ownershipfilepath']
    # A separate script is used in order to log into the service, find the
    # ownership file, and parse it for the ownership hash
    CMD = CHECKS_BIN_PATH + '/telnet_ownership_check {0} {1} {2} {3} {4}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties['ownershipfilepath'],
        )
