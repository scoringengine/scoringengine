import pytest
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team
from scoring_engine.models.service import Service
from scoring_engine.models.check import Check
from scoring_engine.db import session

NUM_TESTBED_SERVICES = 14
NUM_OVERALL_ROUNDS = 5
NUM_OVERALL_TEAMS = 5
SERVICE_TOTAL_POINTS_PER_ROUND = 1425


class TestIntegration(object):
    def test_overall(self):
        blue_teams = Team.get_all_blue_teams()
        assert len(blue_teams) == NUM_OVERALL_TEAMS, \
            "Incorrect number of blue teams"

    def test_round_num(self):
        assert Round.get_last_round_num() == NUM_OVERALL_ROUNDS, \
            "Expecting only {0} of rounds to have run...".format(NUM_OVERALL_ROUNDS)

    @pytest.mark.parametrize("blue_team", Team.get_all_blue_teams())
    def test_blue_teams(self, blue_team):
        assert len(blue_team.services) == NUM_TESTBED_SERVICES, \
            "Invalid number of services enabled per team {0}".format(blue_team.name)
        assert blue_team.current_score == (SERVICE_TOTAL_POINTS_PER_ROUND * NUM_OVERALL_ROUNDS), \
            "Invalid number of overall points per team {0}".format(blue_team.name)

    @pytest.mark.parametrize("service", session.query(Service).all())
    def test_services(self, service):
        assert service.last_check_result() is True, \
            "{0} service failed on {1}".format(service.name, service.team.name)
        assert service.percent_earned == 100

    @pytest.mark.parametrize("check", session.query(Check).all())
    def test_checks(self, check):
        assert check.result is True, \
            "{0} on round {1} failed for team {2}\nReason: {3}\nOutput: {4}".format(check.service.name, check.round.number, check.service.team.name, check.reason, check.output)
