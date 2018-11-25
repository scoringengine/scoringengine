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

                    ]
                },
            ]
        }

    def verify_error(self, error_message):
        with pytest.raises(AssertionError) as error:
            Competition.verify_data(self.setup)
        assert error_message == str(error.value)


class TestTeamsData(CompetitionDataTest):
    def test_no_teams(self):
        del self.setup['teams']
        self.verify_error('teams must be defined on the root')

    def test_teams_type(self):
        self.setup['teams'] = 'a string'
        self.verify_error('teams must be an array')

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


class TestUsersData(CompetitionDataTest):
    def test_user_no_username(self):
        del self.setup['teams'][0]['users'][0]['username']
        self.verify_error("'Team1' user must have a 'username' field")

    def test_user_bad_username(self):
        self.setup['teams'][0]['users'][0]['username'] = []
        self.verify_error("'Team1' user username must a string")

    def test_no_username(self):
        del self.setup['teams'][0]['users'][0]['username']
        self.verify_error("'Team1' user must have a 'username' field")

    def test_bad_username(self):
        self.setup['teams'][0]['users'][0]['username'] = []
        self.verify_error("'Team1' user username must a string")
