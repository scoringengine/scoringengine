"""
Example service configuration:
- name: MongoDB
  check_name: MongoDBCheck
  host: testbed_mongodb
  port: 27017
  accounts:
  - username: ttesterson
    password: testpass
  - username: rpeterson
    password: otherpass
  environments:
  - matching_content: "^SUCCESS"
    properties:
"""
from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class MongoDBCheck(BasicCheck):
    """
    A MongoDB check that is used to verify the uptime and correct function of a
    MongoDB server.
    """
    # Require a
    pass
