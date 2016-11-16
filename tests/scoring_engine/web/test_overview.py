from web_test import WebTest
from scoring_engine.models.team import Team


class TestOverview(WebTest):

    def test_home_no_teams(self):
        resp = self.client.get('/overview')
        assert resp.status_code == 200

    def test_home_with_blue_teams(self):
        team1 = Team(name="Team 1", color="Blue")
        team2 = Team(name="Team 2", color="Blue")
        self.db.save(team1)
        self.db.save(team2)
        resp = self.client.get('/overview')
        assert resp.status_code == 200
