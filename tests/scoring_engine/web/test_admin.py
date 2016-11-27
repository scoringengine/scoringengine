from web_test import WebTest
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

class TestAdmin(WebTest):
    def setup(self):
        super(TestAdmin, self).setup()
        team1 = Team(name="Team 1", color="White")
        self.db.save(team1)
        user1 = User(username='testuser', password='testpass', team=team1)
        self.db.save(user1)

    def auth_and_get_path(self, path):
        self.client.login('testuser', 'testpass')
        return self.client.get(path)

    def test_auth_required_admin(self):
        self.verify_auth_required('/admin')

    def test_auth_required_admin_status(self):
        self.verify_auth_required('/admin/status')
        stats_resp = self.auth_and_get_path('/admin/status')
        assert stats_resp.status_code == 200

    def test_auth_required_admin_manage(self):
        self.verify_auth_required('/admin/manage')
        stats_resp = self.auth_and_get_path('/admin/manage')
        assert stats_resp.status_code == 200

    def test_auth_required_admin_stats(self):
        self.verify_auth_required('/admin/stats')
        stats_resp = self.auth_and_get_path('/admin/stats')
        assert stats_resp.status_code == 200
