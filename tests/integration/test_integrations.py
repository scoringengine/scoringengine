import pytest
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team
from scoring_engine.models.service import Service
from scoring_engine.models.check import Check
from scoring_engine.db import session


@pytest.mark.integration
class TestIntegration:
    def test_overall(self, seeded_db):
        blue_teams = Team.get_all_blue_teams()
        assert len(blue_teams) == seeded_db["num_teams"], "Incorrect number of blue teams"

    def test_round_num(self, seeded_db):
        assert Round.get_last_round_num() == seeded_db["num_rounds"], (
            f"Expecting only {seeded_db['num_rounds']} rounds to have run..."
        )

    def test_blue_teams(self, seeded_db):
        expected_score = (
            seeded_db["num_services"]
            * seeded_db["service_points"]
            * seeded_db["num_rounds"]
        )
        for blue_team in Team.get_all_blue_teams():
            assert len(blue_team.services) == seeded_db["num_services"], (
                f"Invalid number of services enabled per team {blue_team.name}"
            )
            assert blue_team.current_score == expected_score, (
                f"Invalid number of overall points per team {blue_team.name}"
            )

    def test_services(self, seeded_db):
        for service in session.query(Service).all():
            assert service.last_check_result() is True, (
                f"{service.name} service failed on {service.team.name}"
            )
            assert service.percent_earned == 100

    def test_checks(self, seeded_db):
        for check in session.query(Check).all():
            assert check.result is True, (
                f"{check.service.name} on round {check.round.number} failed for team {check.service.team.name}\n"
                f"Reason: {check.reason}\nOutput: {check.output}"
            )
