import pytest

from scoring_engine.competition import Competition


class CompetitionDataTest(object):
    def setup(self):
        self.setup = {
            'teams': [
                {
                    'name': 'Team1',
                    'color': 'Blue',
                    'users': [
                        {
                            'username': 'team1user1',
                            'password': 'testpass'
                        }
                    ],
                    'services': [
                        {
                            'name': 'SSH',
                            'check_name': 'SSHCheck',
                            'host': '127.0.0.1',
                            'port': 22,
                            'points': 150,
                            'accounts': [
                                {
                                    'username': 'ttesterson',
                                    'password': 'testpass'
                                }
                            ],
                            'environments': [
                                {
                                    'matching_regex': '^SUCCESS',
                                    'properties': [
                                        {
                                            'name': 'commands',
                                            'value': 'id;ls -l'
                                        },
                                    ]
                                },
                                {
                                    'matching_regex': 'PID',
                                    'properties': [
                                        {
                                            'name': 'commands',
                                            'value': 'ps'
                                        },
                                    ]
                                }
                            ]
                        }
                    ]
                },
            ]
        }

    def verify_error(self, error_message):
        with pytest.raises(AssertionError) as error:
            Competition(self.setup)
        assert error_message == str(error.value)


class TestRootData(CompetitionDataTest):
    def test_no_teams(self):
        del self.setup['teams']
        self.verify_error('teams must be defined on the root')

    def test_teams_type(self):
        self.setup['teams'] = 'a string'
        self.verify_error('teams must be an array')


class TestTeamsData(CompetitionDataTest):

    def test_team_no_name(self):
        del self.setup['teams'][0]['name']
        self.verify_error("team must have a 'name' field")

    def test_team_bad_name_type(self):
        self.setup['teams'][0]['name'] = []
        self.verify_error('team name must be a string')

    def test_team_no_color(self):
        del self.setup['teams'][0]['color']
        self.verify_error("'Team1' must have a 'color' field")

    def test_team_bad_color_type(self):
        self.setup['teams'][0]['color'] = []
        self.verify_error("'Team1' color must a string")

    def test_team_bad_color_value(self):
        self.setup['teams'][0]['color'] = 'Green'
        self.verify_error("'Team1' color must one of (Red, White, Blue)")

    def test_team_no_users(self):
        del self.setup['teams'][0]['users']
        self.verify_error("'Team1' must have a 'users' field")

    def test_users_bad_type(self):
        self.setup['teams'][0]['users'] = 'a string'
        self.verify_error("'Team1' 'users' field must be an array")

    def test_team_no_services(self):
        del self.setup['teams'][0]['services']
        self.verify_error("'Team1' must have a 'services' field")

    def test_team_bad_services_type(self):
        self.setup['teams'][0]['services'] = 'a string'
        self.verify_error("'Team1' 'services' field must be an array")


class TestUserData(CompetitionDataTest):
    def test_no_username(self):
        del self.setup['teams'][0]['users'][0]['username']
        self.verify_error("Team1 user must have a 'username' field")

    def test_user_bad_username(self):
        self.setup['teams'][0]['users'][0]['username'] = []
        self.verify_error("Team1 user username must a string")

    def test_no_password(self):
        del self.setup['teams'][0]['users'][0]['password']
        self.verify_error("Team1 user must have a 'password' field")

    def test_bad_password(self):
        self.setup['teams'][0]['users'][0]['username'] = []
        self.verify_error("Team1 user username must a string")


class TestServiceData(CompetitionDataTest):
    def test_no_name(self):
        del self.setup['teams'][0]['services'][0]['name']
        self.verify_error("Team1 service must have a 'name' field")

    def test_bad_name_type(self):
        self.setup['teams'][0]['services'][0]['name'] = []
        self.verify_error("Team1 service 'name' must be a string")

    def test_no_check_name(self):
        del self.setup['teams'][0]['services'][0]['check_name']
        self.verify_error("Team1 SSH service must have a 'check_name' field")

    def test_bad_check_name_type(self):
        self.setup['teams'][0]['services'][0]['check_name'] = []
        self.verify_error("Team1 SSH service 'check_name' field must be a string")

    def test_bad_check_name_value(self):
        self.setup['teams'][0]['services'][0]['check_name'] = 'SomeCheck'
        self.verify_error("Team1 SSH Incorrect 'check_name' field, must match the classname of a check defined in scoring_engine/checks")

    def test_no_host(self):
        del self.setup['teams'][0]['services'][0]['host']
        self.verify_error("Team1 SSH service must have a 'host' field")

    def test_bad_host_type(self):
        self.setup['teams'][0]['services'][0]['host'] = []
        self.verify_error("Team1 SSH service 'host' field must be a string")

    def test_no_port(self):
        del self.setup['teams'][0]['services'][0]['port']
        self.verify_error("Team1 SSH service must have a 'port' field")

    def test_bad_port_type(self):
        self.setup['teams'][0]['services'][0]['port'] = 'a string'
        self.verify_error("Team1 SSH service 'port' field must be an integer")

    def test_no_points(self):
        del self.setup['teams'][0]['services'][0]['points']
        self.verify_error("Team1 SSH service must have a 'points' field")

    def test_bad_points_type(self):
        self.setup['teams'][0]['services'][0]['points'] = 'a string'
        self.verify_error("Team1 SSH service 'points' field must be an integer")

    def test_bad_accounts_type(self):
        self.setup['teams'][0]['services'][0]['accounts'] = 'a string'
        self.verify_error("Team1 SSH service 'accounts' field must be an array")

    def test_no_environments(self):
        del self.setup['teams'][0]['services'][0]['environments']
        self.verify_error("Team1 SSH service must have a 'environments' field")

    def test_bad_environments_type(self):
        self.setup['teams'][0]['services'][0]['environments'] = 'a string'
        self.verify_error("Team1 SSH service 'environments' field must be an array")


class TestAccountData(CompetitionDataTest):
    def test_no_username(self):
        del self.setup['teams'][0]['services'][0]['accounts'][0]['username']
        self.verify_error("Team1 SSH account must have a 'username' field")

    def test_bad_username_type(self):
        self.setup['teams'][0]['services'][0]['accounts'][0]['username'] = []
        self.verify_error("Team1 SSH account 'username' field must be a string")

    def test_no_password(self):
        del self.setup['teams'][0]['services'][0]['accounts'][0]['password']
        self.verify_error("Team1 SSH account must have a 'password' field")

    def test_bad_password_type(self):
        self.setup['teams'][0]['services'][0]['accounts'][0]['password'] = []
        self.verify_error("Team1 SSH account 'password' field must be a string")


class TestEnvironmentData(CompetitionDataTest):
    def test_no_matching_regex(self):
        del self.setup['teams'][0]['services'][0]['environments'][0]['matching_regex']
        self.verify_error("Team1 SSH environment must have a 'matching_regex' field")

    def test_bad_matching_regex_type(self):
        self.setup['teams'][0]['services'][0]['environments'][0]['matching_regex'] = []
        self.verify_error("Team1 SSH environment 'matching_regex' field must be a string")

    def test_bad_properties_type(self):
        self.setup['teams'][0]['services'][0]['environments'][0]['properties'] = 'a string'
        self.verify_error("Team1 SSH environment 'properties' field must be an array")


class TestPropertyData(CompetitionDataTest):
    def test_no_name(self):
        del self.setup['teams'][0]['services'][0]['environments'][0]['properties'][0]['name']
        self.verify_error("Team1 SSH property must have a 'name' field")

    def test_bad_name_type(self):
        self.setup['teams'][0]['services'][0]['environments'][0]['properties'][0]['name'] = []
        self.verify_error("Team1 SSH property 'name' field must be a string")

    def test_no_value(self):
        del self.setup['teams'][0]['services'][0]['environments'][0]['properties'][0]['value']
        self.verify_error("Team1 SSH property must have a 'value' field")

    def test_bad_value_type(self):
        self.setup['teams'][0]['services'][0]['environments'][0]['properties'][0]['value'] = []
        self.verify_error("Team1 SSH property 'value' field must be a string")

    def test_bad_name_value(self):
        self.setup['teams'][0]['services'][0]['environments'][0]['properties'][0]['name'] = 'someproperty'
        self.verify_error("Team1 SSH SSHCheck does not require the property 'someproperty'")

    def test_all_required_properties(self):
        del self.setup['teams'][0]['services'][0]['environments'][0]['properties'][0]
        self.verify_error("Team1 SSH service does not define the 'commands' property")


class TestGoodSetup(CompetitionDataTest):
    # This verifies that the good setup is parseable
    def test_good_setup_parses(self):
        Competition(self.setup)