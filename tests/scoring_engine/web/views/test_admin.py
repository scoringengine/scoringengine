from tests.scoring_engine.web.web_test import WebTest
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.service import Service


class TestAdmin(WebTest):
    def setup(self):
        super(TestAdmin, self).setup()
        user = self.create_default_user()
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", host='127.0.0.1', team=user.team)
        self.session.add(service)
        self.session.commit()

    def unauthorized_admin_test(self, path):
        red_team = Team(name="Red Team", color="Red")
        self.session.add(red_team)
        user = User(username="testuser_red", password="testpass_red", team=red_team)
        self.session.add(user)
        self.session.commit()
        self.login('testuser_red', 'testpass_red')
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

    def test_auth_required_admin_workers(self):
        self.verify_auth_required('/admin/workers')
        stats_resp = self.auth_and_get_path('/admin/workers')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_workers(self):
        self.unauthorized_admin_test('/admin/workers')

    def test_auth_required_admin_queues(self):
        self.verify_auth_required('/admin/queues')
        stats_resp = self.auth_and_get_path('/admin/queues')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_queues(self):
        self.unauthorized_admin_test('/admin/queues')

    def test_auth_required_admin_manage(self):
        self.verify_auth_required('/admin/manage')
        stats_resp = self.auth_and_get_path('/admin/manage')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_manage(self):
        self.unauthorized_admin_test('/admin/manage')

    def test_auth_required_admin_permissions(self):
        self.verify_auth_required('/admin/permissions')
        stats_resp = self.auth_and_get_path('/admin/permissions')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_permissions(self):
        self.unauthorized_admin_test('/admin/permissions')

    def test_auth_required_admin_settings(self):
        self.verify_auth_required('/admin/settings')
        stats_resp = self.auth_and_get_path('/admin/settings')
        assert stats_resp.status_code == 200

    def test_auth_bad_auth_settings(self):
        self.unauthorized_admin_test('/admin/settings')

    def test_auth_required_admin_service(self):
        self.verify_auth_required('/admin/service/1')
        stats_resp = self.auth_and_get_path('/admin/service/1')
        assert stats_resp.status_code == 200

    def test_admin_bad_service(self):
        self.verify_auth_required('/admin/service/200')
        resp = self.auth_and_get_path('/admin/service/200')
        assert resp.status_code == 302
        assert 'unauthorized' in str(resp.data)

    def test_auth_bad_auth_team(self):
        self.unauthorized_admin_test('/admin/service/3')
