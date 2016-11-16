from web_test import WebTest


class TestAuth(WebTest):

    def test_login_page(self):
        resp = self.client.get('/login')
        assert resp.status_code == 200

    def test_auth_required_logout(self):
        self.verify_auth_required('/logout')
