from web_test import WebTest


class TestAdmin(WebTest):

    def test_auth_required_api_admin_get_round_progress(self):
        self.verify_auth_required('/api/admin/get_round_progress')

    def test_auth_required_api_admin_get_teams(self):
        self.verify_auth_required('/api/admin/get_teams')

    def test_auth_required_api_admin_update_password(self):
        self.verify_auth_required_post('/api/admin/update_password')

    def test_auth_required_api_admin_add_user(self):
        self.verify_auth_required_post('/api/admin/add_user')

    def test_auth_required_api_profile_update_password(self):
        self.verify_auth_required_post('/api/profile/update_password')

    def test_auth_required_api_service_get_checks_id(self):
        self.verify_auth_required('/api/service/get_checks/1')
