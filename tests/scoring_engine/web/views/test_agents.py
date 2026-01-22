from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from tests.scoring_engine.web.web_test import WebTest


class TestAgents(WebTest):

    def setup_method(self):
        super(TestAgents, self).setup_method()
        # Clear the Setting cache to ensure fresh lookups
        Setting.clear_cache()

    def test_debug(self):
        assert type(self.app.debug) is bool

    def test_agents_redirects_without_psk(self):
        """When agent_psk is not set, /agents should redirect to home"""
        Setting.clear_cache()
        resp = self.client.get("/agents")
        assert resp.status_code == 302
        assert "/index" in resp.location or resp.location == "/"

    def test_agents_redirects_with_empty_psk(self):
        """When agent_psk is empty string, /agents should redirect to home"""
        self.session.add(Setting(name="agent_psk", value=""))
        self.session.commit()
        Setting.clear_cache()
        resp = self.client.get("/agents")
        assert resp.status_code == 302
        assert "/index" in resp.location or resp.location == "/"

    def test_agents_accessible_with_psk(self):
        """When agent_psk is set, /agents should be accessible"""
        self.session.add(Setting(name="agent_psk", value="secret_key_123"))
        self.session.commit()
        Setting.clear_cache()
        resp = self.client.get("/agents")
        assert resp.status_code == 200
        assert self.mock_obj.call_args == self.build_args("agents.html", teams=[])

    def test_agents_shows_teams(self):
        """When agent_psk is set and teams exist, they should be passed to template"""
        self.session.add(Setting(name="agent_psk", value="secret_key_123"))
        team1 = Team(name="Team 1", color="Blue")
        team2 = Team(name="Team 2", color="Blue")
        self.session.add(team1)
        self.session.add(team2)
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.get("/agents")
        assert resp.status_code == 200
        # Check that teams were passed to template
        call_kwargs = self.mock_obj.call_args[1]
        assert len(call_kwargs["teams"]) == 2
