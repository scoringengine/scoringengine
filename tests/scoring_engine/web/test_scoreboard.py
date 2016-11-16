from web_test import WebTest


class TestScoreboard(WebTest):

    def test_home(self):
        resp = self.client.get('/scoreboard')
        assert resp.status_code == 200
