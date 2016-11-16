from web_test import WebTest


class TestServices(WebTest):

    def test_home(self):
        resp = self.client.get('/services')
        assert resp.status_code == 302

    def test_auth_required(self):
        resp = self.client.get('/service/1')
        assert resp.status_code == 302
        assert '/login?' in resp.location
