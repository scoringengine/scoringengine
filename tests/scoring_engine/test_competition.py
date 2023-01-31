import pytest
import copy

from scoring_engine.models.team import Team
from scoring_engine.competition import Competition

from tests.scoring_engine.unit_test import UnitTest


class CompetitionDataTest(UnitTest):
    def setup(self):
        super(CompetitionDataTest, self).setup()
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
                                },
                                {
                                    'username': 'rpeterson',
                                    'password': 'redfred'
                                }
                            ],
                            'environments': [
                                {
                                    'matching_content': '^SUCCESS',
                                    'properties': [
                                        {
                                            'name': 'commands',
                                            'value': 'id;ls -l'
                                        },
                                    ]
                                },
                                {
                                    'matching_content': 'PID',
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
                {
                    'name': 'WhiteTeam',
                    'color': 'White',
                    'users': [
                        {
                            'username': 'whiteteamuser',
                            'password': 'testpass'
                        }
                    ]
                },
                {
                    'name': 'RedTeam',
                    'color': 'Red',
                    'users': [
                        {
                            'username': 'redteamuser',
                            'password': 'testpass'
                        }
                    ]
                },
            ],
            'flags': [],  # TODO - Populate this with test flags
        }

    def verify_error(self, error_message):
        with pytest.raises(AssertionError) as error:
            Competition(self.setup)
        assert error_message == str(error.value)


class TestYAMLParse(CompetitionDataTest):
    def test_parse_yaml_str(self):
        yaml_str = """
---
teams:
- name: WhiteTeam
  color: White
  users:
  - username: whiteteamuser
    password: testpass
        """
        competition = Competition.parse_yaml_str(yaml_str)
        assert len(competition['teams']) == 1


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

    def test_team_duplicate_services_name(self):
        self.setup['teams'][0]['services'][0]['name'] = 'Test'
        new_service = copy.deepcopy(self.setup['teams'][0]['services'][0])
        self.setup['teams'][0]['services'].append(new_service)
        self.verify_error("Each team's service must have a unique name, found duplicates in 'Test' for team 'Team1'")

    def test_team_missing_service(self):
        new_service = copy.deepcopy(self.setup['teams'][0]['services'][0])
        new_service['name'] = 'Service2'
        self.setup['teams'][0]['services'].append(new_service)

        second_team = copy.deepcopy(self.setup['teams'][0])
        second_team['name'] = 'Team 2'
        second_team['services'][0]['name'] = 'OtherService'
        self.setup['teams'].append(second_team)
        self.verify_error("Service 'SSH' not defined in team 'Team 2'")

    def test_team_additional_service(self):
        second_team = copy.deepcopy(self.setup['teams'][0])
        second_team['name'] = 'Team 2'
        new_service = copy.deepcopy(second_team['services'][0])
        new_service['name'] = 'Service2'
        second_team['services'].append(new_service)
        self.setup['teams'].append(second_team)
        self.verify_error("Service 'Service2' for Team 'Team 2' not defined in other teams")

    def test_team_different_service_check_name(self):
        second_team = copy.deepcopy(self.setup['teams'][0])
        second_team['name'] = 'Team 2'
        second_team['services'][0]['check_name'] = 'ICMPCheck'
        second_team['services'][0]['environments'] = [{'matching_content': '^SUCCESS'}]
        self.setup['teams'].append(second_team)
        self.verify_error("Incorrect check_name for Service 'SSH' for Team 'Team 2'. Got: 'ICMPCheck' Expected: SSHCheck")

    def test_team_different_service_points(self):
        second_team = copy.deepcopy(self.setup['teams'][0])
        second_team['name'] = 'Team 2'
        second_team['services'][0]['points'] = 5
        self.setup['teams'].append(second_team)
        self.verify_error("Incorrect points for Service 'SSH' for Team 'Team 2'. Got: 5 Expected: 150")


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

    def test_duplicate_users(self):
        self.setup['teams'][0]['users'].append({'username': 'team1user1', 'password': 'somepassword'})
        self.verify_error("Multiple Users with the same username: 'team1user1'")


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

    def test_bad_worker_queue(self):
        self.setup['teams'][0]['services'][0]['worker_queue'] = []
        self.verify_error("Team1 SSH service 'worker_queue' field must be a string")


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
    def test_no_matching_content(self):
        del self.setup['teams'][0]['services'][0]['environments'][0]['matching_content']
        self.verify_error("Team1 SSH environment must have a 'matching_content' field")

    def test_bad_matching_content_type(self):
        self.setup['teams'][0]['services'][0]['environments'][0]['matching_content'] = []
        self.verify_error("Team1 SSH environment 'matching_content' field must be a string")

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
    # Test to make sure we can parse a good json correctly
    # and can write all the things to the db
    def setup(self):
        super(TestGoodSetup, self).setup()
        competition = Competition(self.setup)
        competition.save(self.session)
        self.blue_teams = Team.get_all_blue_teams()
        self.blue_team = self.blue_teams[0]
        self.service = self.blue_team.services[0]
        self.account = self.service.accounts[0]
        self.environment = self.service.environments[0]
        self.property = self.environment.properties[0]

    def test_teams(self):
        assert len(self.session.query(Team).all()) == 3
        assert len(self.blue_teams) == 1

    def test_blue_team(self):
        assert self.blue_team.name == 'Team1'
        assert len(self.blue_team.users) == 1
        assert len(self.blue_team.services) == 1

    def test_service(self):
        assert self.service.name == 'SSH'
        assert self.service.check_name == 'SSHCheck'
        assert self.service.host == '127.0.0.1'
        assert self.service.port == 22
        assert self.service.points == 150
        assert len(self.service.accounts) == 2
        assert len(self.service.environments) == 2

    def test_account(self):
        assert self.account.username == 'ttesterson'
        assert self.account.password == 'testpass'

    def test_environment(self):
        assert self.environment.matching_content == '^SUCCESS'
        assert len(self.environment.properties) == 1

    def test_property(self):
        assert self.property.name == 'commands'
        assert self.property.value == 'id;ls -l'
