from web_test import WebTest


class TestAdmin(WebTest):
    def setup(self):
        super(TestAdmin, self).setup()
        self.create_default_user()

    def test_auth_required_admin(self):
        self.verify_auth_required('/admin')
        stats_resp = self.auth_and_get_path('/admin')
        assert stats_resp.status_code == 200

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
