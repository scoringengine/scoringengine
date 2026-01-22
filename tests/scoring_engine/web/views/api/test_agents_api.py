import json

from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from tests.scoring_engine.unit_test import UnitTest


class TestAgentsAPI(UnitTest):

    def setup_method(self):
        super(TestAgentsAPI, self).setup_method()
        self.client = self.app.test_client()

    def test_agents_get_columns_empty(self):
        """Test get_columns with no teams"""
        resp = self.client.get("/api/agents/get_columns")
        assert resp.status_code == 200
        data = json.loads(resp.data.decode("utf8"))
        # Should have just the empty first column
        assert data["columns"] == [{"title": "", "data": ""}]

    def test_agents_get_columns_with_teams(self):
        """Test get_columns with blue teams"""
        team1 = Team(name="Team Alpha", color="Blue")
        team2 = Team(name="Team Beta", color="Blue")
        red_team = Team(name="Red Team", color="Red")
        self.session.add_all([team1, team2, red_team])
        self.session.commit()

        resp = self.client.get("/api/agents/get_columns")
        assert resp.status_code == 200
        data = json.loads(resp.data.decode("utf8"))
        # Should have empty column plus blue team columns (not red team)
        assert len(data["columns"]) == 3
        assert data["columns"][0] == {"title": "", "data": ""}
        assert data["columns"][1] == {"title": "Team Alpha", "data": "Team Alpha"}
        assert data["columns"][2] == {"title": "Team Beta", "data": "Team Beta"}

    def test_agents_get_data_empty(self):
        """Test get_data with no teams returns empty data"""
        resp = self.client.get("/api/agents/get_data")
        assert resp.status_code == 200
        data = json.loads(resp.data.decode("utf8"))
        assert data["data"] == []

    def test_agents_get_data_no_rounds(self):
        """Test get_data with teams but no rounds returns empty data"""
        team1 = Team(name="Team 1", color="Blue")
        self.session.add(team1)
        self.session.commit()

        resp = self.client.get("/api/agents/get_data")
        assert resp.status_code == 200
        data = json.loads(resp.data.decode("utf8"))
        assert data["data"] == []

    def test_agents_get_data_with_agent_checks(self):
        """Test get_data returns agent check results"""
        # Create teams
        team1 = Team(name="Team 1", color="Blue")
        team2 = Team(name="Team 2", color="Blue")
        self.session.add_all([team1, team2])
        self.session.commit()

        # Create agent services
        agent1_t1 = Service(
            name="Agent HOST1",
            team=team1,
            check_name="AgentCheck",
            host="HOST1",
        )
        agent1_t2 = Service(
            name="Agent HOST1",
            team=team2,
            check_name="AgentCheck",
            host="HOST1",
        )
        agent2_t1 = Service(
            name="Agent HOST2",
            team=team1,
            check_name="AgentCheck",
            host="HOST2",
        )
        # Also create a non-agent service (should not appear in results)
        http_service = Service(
            name="HTTP",
            team=team1,
            check_name="HTTPCheck",
            host="webserver",
            port=80,
        )
        self.session.add_all([agent1_t1, agent1_t2, agent2_t1, http_service])
        self.session.commit()

        # Create round and checks
        round1 = Round(number=1)
        self.session.add(round1)
        self.session.commit()

        # Agent checks
        check1 = Check(round=round1, service=agent1_t1, result=True, output="ok")
        check2 = Check(round=round1, service=agent1_t2, result=False, output="fail")
        check3 = Check(round=round1, service=agent2_t1, result=True, output="ok")
        # HTTP check (should not appear)
        check4 = Check(round=round1, service=http_service, result=True, output="ok")
        self.session.add_all([check1, check2, check3, check4])
        self.session.commit()

        resp = self.client.get("/api/agents/get_data")
        assert resp.status_code == 200
        data = json.loads(resp.data.decode("utf8"))

        # Should have 2 rows (HOST1 and HOST2)
        assert len(data["data"]) == 2

        # Data should be sorted by host
        # HOST1: Team1=True, Team2=False
        # HOST2: Team1=True, Team2=None (no agent)
        host1_row = data["data"][0]
        host2_row = data["data"][1]

        assert host1_row[0] == "HOST1"
        assert host1_row[1] is True  # Team 1
        assert host1_row[2] is False  # Team 2

        assert host2_row[0] == "HOST2"
        assert host2_row[1] is True  # Team 1
        assert host2_row[2] is None  # Team 2 has no agent on HOST2

    def test_agents_get_data_uses_latest_round(self):
        """Test that get_data uses the latest round's results"""
        team1 = Team(name="Team 1", color="Blue")
        self.session.add(team1)
        self.session.commit()

        agent = Service(
            name="Agent",
            team=team1,
            check_name="AgentCheck",
            host="HOST1",
        )
        self.session.add(agent)
        self.session.commit()

        # Create two rounds with different results
        round1 = Round(number=1)
        round2 = Round(number=2)
        self.session.add_all([round1, round2])
        self.session.commit()

        check1 = Check(round=round1, service=agent, result=False, output="fail")
        check2 = Check(round=round2, service=agent, result=True, output="ok")
        self.session.add_all([check1, check2])
        self.session.commit()

        resp = self.client.get("/api/agents/get_data")
        data = json.loads(resp.data.decode("utf8"))

        # Should show the result from the latest round (round 2)
        assert len(data["data"]) == 1
        assert data["data"][0][0] == "HOST1"
        assert data["data"][0][1] is True  # Latest result is True
