from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.unit_test import UnitTest


class TestTeamAPI(UnitTest):
    def setup_method(self):
        super(TestTeamAPI, self).setup_method()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

        self.blue_team_1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team_2 = Team(name="Blue Team 2", color="Blue")
        self.session.add_all([self.blue_team_1, self.blue_team_2])
        self.session.commit()

        self.blue_user_1 = User(username="blue_user_1", password="pass", team=self.blue_team_1)
        self.blue_user_2 = User(username="blue_user_2", password="pass", team=self.blue_team_2)
        self.session.add_all([self.blue_user_1, self.blue_user_2])
        self.session.commit()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def test_team_machines_returns_distinct_hosts_for_team(self):
        self.session.add_all(
            [
                Service(name="Web", check_name="HTTPCheck", host="host-a", port=80, team=self.blue_team_1),
                Service(name="DNS", check_name="DNSCheck", host="host-b", port=53, team=self.blue_team_1),
                Service(name="SSH", check_name="SSHCheck", host="host-c", port=22, team=self.blue_team_1),
                Service(name="Other Team Host", check_name="HTTPCheck", host="host-z", port=80, team=self.blue_team_2),
            ]
        )
        self.session.commit()

        self.login("blue_user_1", "pass")
        resp = self.client.get(f"/api/team/{self.blue_team_1.id}/machines")

        assert resp.status_code == 200
        assert resp.json == {"data": [{"host": "host-a"}, {"host": "host-b"}, {"host": "host-c"}]}

    def test_team_machines_rejects_other_teams(self):
        self.login("blue_user_1", "pass")
        resp = self.client.get(f"/api/team/{self.blue_team_2.id}/machines")

        assert resp.status_code == 403
        assert resp.json == {"status": "Unauthorized"}
