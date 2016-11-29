from web_test import WebTest


class TestProfile(WebTest):

    def test_home_auth_required(self):
        self.verify_auth_required('/profile')

    def test_home_with_auth(self):
        self.create_default_user()
        self.client.login('testuser', 'testpass')
        resp = self.auth_and_get_path('/profile')
        assert resp.status_code == 200
