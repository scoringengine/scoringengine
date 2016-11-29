from web_test import WebTest


class TestWelcome(WebTest):

    view_name = 'welcome'

    def test_home(self):
        resp = self.client.get('/')
        assert self.mock_obj.call_args == self.build_args('welcome.html')
        assert resp.status_code == 200

    def test_home_index(self):
        resp = self.client.get('/index')
        assert self.mock_obj.call_args == self.build_args('welcome.html')
        assert resp.status_code == 200
