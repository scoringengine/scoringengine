from tests.scoring_engine.web.web_test import WebTest
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestAdmin(WebTest):
    def setup(self):
        super(TestAdmin, self).setup()
        self.create_default_user()

    def unauthorized_admin_test(self, path):
        red_team = Team(name="Red Team", color="Red")
        self.session.add(red_team)
        user = User(username="testuser_red", password="testpass_red", team=red_team)
        self.session.add(user)
        self.session.commit()
        self.client.login('testuser_red', 'testpass_red')
        resp = self.client.get(path)
        assert resp.status_code == 302
        assert 'unauthorized' in str(resp.data)

    def test_auth_required_admin(self):
        self.verify_auth_required('/admin')
        stats_resp = self.auth_and_get_path('/admin')
        assert stats_resp.status_code == 200

    def test_auth_required_admin_status(self):
        self.verify_auth_required('/admin/status')
        stats_resp = self.auth_and_get_path('/admin/status')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_status(self):
        self.unauthorized_admin_test('/admin/status')

    def test_auth_required_admin_manage(self):
        self.verify_auth_required('/admin/manage')
        stats_resp = self.auth_and_get_path('/admin/manage')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_manage(self):
        self.unauthorized_admin_test('/admin/manage')

    def test_auth_required_admin_settings(self):
        self.verify_auth_required('/admin/settings')
        stats_resp = self.auth_and_get_path('/admin/settings')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_settings(self):
        self.unauthorized_admin_test('/admin/settings')

    def test_auth_required_admin_progress(self):
        self.verify_auth_required('/admin/progress')
        stats_resp = self.auth_and_get_path('/admin/progress')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_progress(self):
        self.unauthorized_admin_test('/admin/progress')

    def test_auth_required_admin_team(self):
        self.verify_auth_required('/admin/team/1')
        stats_resp = self.auth_and_get_path('/admin/team/1')
        assert stats_resp.status_code == 200

    def test_admin_bad_team(self):
        self.verify_auth_required('/admin/team/20')
        resp = self.auth_and_get_path('/admin/team/20')
        assert resp.status_code == 302
        assert 'unauthorized' in str(resp.data)

    def test_auth_bad_auth_team(self):
        self.unauthorized_admin_test('/admin/team/3')
