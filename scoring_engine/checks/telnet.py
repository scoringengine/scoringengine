"""
Example service configuration:
- name: Telnet
  check_name: TelnetCheck
  host: testbed_telnet
  port: 23
  points: 25
  accounts:
  - username: ttesterson
    password: testpass
  environments:
  - matching_content: "^SUCCESS"
    properties:
    - name: commands
      value: id;ls -l /home
"""
from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class TelnetCheck(BasicCheck):
    """
    A Telnet check that is used to verify the uptime and correct function of a
    Telnet service.
    """
    # Require a list of commands, separated by semicolons
    required_properties = ['commands']
    # A separate script is used in order to log into the service, run the
    # commands, and make sure there were no errors
    CMD = CHECKS_BIN_PATH + '/telnet_check {0} {1} {2} {3} {4}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties['commands'],
        )
