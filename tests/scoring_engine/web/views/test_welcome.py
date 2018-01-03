from tests.scoring_engine.web.web_test import WebTest


class TestWelcome(WebTest):

    def setup(self):
        super(TestWelcome, self).setup()
        self.create_default_user()
        self.welcome_content = 'example welcome content <br>here'

    def test_home(self):
        resp = self.client.get('/')
        assert self.mock_obj.call_args == self.build_args('welcome.html', welcome_content=self.welcome_content)
        assert resp.status_code == 200

    def test_home_index(self):
        resp = self.client.get('/index')
        assert self.mock_obj.call_args == self.build_args('welcome.html', welcome_content=self.welcome_content)
        assert resp.status_code == 200
