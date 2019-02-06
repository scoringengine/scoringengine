"""
Example service configuration:
- name: KOTH-SSH
  check_name: SSHCheck
  host: testbed_koth_ssh
  port: 22
  points: 25
  accounts:
  - username: ttesterson
    password: testpass
  - username: rpeterson
    password: otherpass
  environments:
  - matching_content: "^SUCCESS"
    properties:
    - name: commands
      value: id;ls -l /home
    - name: ownershipfilepath
      value: ~/ownership.txt
"""
from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class SSHOwnershipCheck(BasicCheck):
    """
    An SSH check for King of the Hill competitions that is used to determine
    which team has ownership over the service.
    """
    # We need to know where to find the ownership file
    required_properties = ['ownershipfilepath']
    # A separate script is used in order log into the service, find the
    # ownership file, and parse it for the ownership hash
    CMD = CHECKS_BIN_PATH + '/ssh_ownership_check {0} {1} {2} {3} {4}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties['ownershipfilepath']
        )
