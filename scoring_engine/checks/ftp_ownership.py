"""
Example service configuration:
- name: KOTH-FTP
  check_name: FTPCheck
  host: testbed_koth_ftp
  port: 21
  points: 25
  accounts:
  - username: ttesterson
    password: testpass
  environments:
  - matching_content: "^SUCCESS"
    properties:
    - name: remotefilepath
      value: "/ftp_files/testfile.txt"
    - name: filecontents
      value: Sample file content
    - name: ownershipfilepath
      value: "/ftp_files/ownership.txt"
"""
from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class FTPOwnershipCheck(BasicCheck):
    """
    An FTP check for King of the Hill competitions that is used to determine
    which team has ownership over the service.
    """
    # We only need to know where to find the ownership file
    required_properties = ['ownershipfilepath']
    # A separate script is used in order to find the file and parse the
    # contents for the ownership hash
    CMD = CHECKS_BIN_PATH + '/ftp_ownership_check {0} {1} {2} {3} {4}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties['ownershipfilepath'],
        )
