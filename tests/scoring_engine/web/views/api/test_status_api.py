from scoring_engine.models.machines import Machine
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.unit_test import UnitTest


class TestStatusAPI(UnitTest):
    def setup_method(self):
        super(TestStatusAPI, self).setup_method()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

        self.white_team = Team(name="White Team", color="White")
        self.red_team = Team(name="Red Team", color="Red")
        self.blue_team_1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team_2 = Team(name="Blue Team 2", color="Blue")
        self.green_team = Team(name="Green Team", color="Green")
        self.session.add_all(
            [self.white_team, self.red_team, self.blue_team_1, self.blue_team_2, self.green_team]
        )
        self.session.commit()

        self.white_user = User(username="whiteuser", password="pass", team=self.white_team)
        self.red_user = User(username="reduser", password="pass", team=self.red_team)
        self.blue_user_1 = User(username="blueuser1", password="pass", team=self.blue_team_1)
        self.blue_user_2 = User(username="blueuser2", password="pass", team=self.blue_team_2)
        self.green_user = User(username="greenuser", password="pass", team=self.green_team)
        self.session.add_all(
            [self.white_user, self.red_user, self.blue_user_1, self.blue_user_2, self.green_user]
        )
        self.session.commit()

        self.session.add_all(
            [
                Machine(name="alpha", team_id=self.blue_team_1.id, status="healthy", compromised=False),
                Machine(name="bravo", team_id=self.blue_team_1.id, status="offline", compromised=False),
                Machine(name="charlie", team_id=self.blue_team_2.id, status="compromised", compromised=True),
            ]
        )
        self.session.commit()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def test_api_status_requires_auth(self):
        resp = self.client.get("/api/status")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_api_status_white_team_sees_all_machine_fields(self):
        self.login("whiteuser", "pass")
        resp = self.client.get("/api/status")

        assert resp.status_code == 200
        data = resp.json["data"]
        assert len(data) == 3

        for machine in data:
            assert set(machine.keys()) == {"id", "team_id", "name", "status", "compromised"}

    def test_api_status_red_team_sees_all(self):
        self.login("reduser", "pass")
        resp = self.client.get("/api/status")

        assert resp.status_code == 200
        assert len(resp.json["data"]) == 3

    def test_api_status_blue_team_only_sees_own(self):
        self.login("blueuser1", "pass")
        resp = self.client.get("/api/status")

        assert resp.status_code == 200
        data = resp.json["data"]
        assert len(data) == 2
        assert [m["name"] for m in data] == ["alpha", "bravo"]
        assert all(m["team_id"] == self.blue_team_1.id for m in data)

    def test_api_status_unknown_role_forbidden(self):
        self.login("greenuser", "pass")
        resp = self.client.get("/api/status")

        assert resp.status_code == 403
        assert resp.json == {"status": "Unauthorized"}
