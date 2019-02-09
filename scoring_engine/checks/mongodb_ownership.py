"""
Example service configuration:
- name: KOTH-MongoDB
  check_name: MongoDBCheck
  host: testbed_koth_mongodb
  port: 27017
  points: 25
  accounts:
  - username: ttesterson
    password: testpass
  environments:
  - matching_content: "^SUCCESS"
    properties:
    - name: database
      value: test
"""
from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class MongoDBOwnershipCheck(BasicCheck):
    """
    A MongoDB check for King of the Hill that is used to determine which team
    has ownership over the service.
    """
    # Require a database that the user will be able to read from
    required_properties = ['database']
    CMD = CHECKS_BIN_PATH + '/mongodb_ownership_check {0} {1} {2} {3} {4}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties['database'],
        )
