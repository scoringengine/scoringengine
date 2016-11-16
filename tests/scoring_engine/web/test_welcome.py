from web_test import WebTest


class TestWelcome(WebTest):

    def test_home(self):
        resp = self.client.get('/')
        assert resp.status_code == 200

    def test_home_index(self):
        resp = self.client.get('/index')
        assert resp.status_code == 200
