from web_test import WebTest


class TestAuth(WebTest):

    def test_login_page_auth_required(self):
        resp = self.client.get('/login')
        assert resp.status_code == 200

    def test_unauthorized(self):
        resp = self.client.get('/unauthorized')
        assert resp.status_code == 200

    def test_auth_required_logout(self):
        self.verify_auth_required('/logout')

    def test_login_logout(self):
        user = self.create_default_user()
        assert user.authenticated is False
        self.auth_and_get_path('/')
        assert user.authenticated is True
        logout_resp = self.client.get('/logout')
        assert user.authenticated is False
        assert logout_resp.status_code == 302
        self.verify_auth_required('/services')
