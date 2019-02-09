"""
Example service configuration:
- name: MongoDB
  check_name: MongoDBCheck
  host: testbed_mongodb
  port: 27017
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


class MongoDBCheck(BasicCheck):
    """
    A MongoDB check that is used to verify the uptime and correct function of a
    MongoDB server.
    """
    # Require a database that the user will be able to read and write to
    required_properties = ['database']
    CMD = CHECKS_BIN_PATH + '/mongodb_check {0} {1} {2} {3} {4}'

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            account.password,
            properties['database'],
        )
