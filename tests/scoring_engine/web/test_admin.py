from web_test import WebTest


class TestAdmin(WebTest):

    def test_auth_required_admin(self):
        self.verify_auth_required('/admin')

    def test_auth_required_admin_status(self):
        self.verify_auth_required('/admin/status')

    def test_auth_required_admin_manage(self):
        self.verify_auth_required('/admin/manage')

    def test_auth_required_admin_stats(self):
        self.verify_auth_required('/admin/stats')

    def test_auth_required_admin_api_get_progress_total(self):
        self.verify_auth_required('/admin/api/get_progress/total')
