from tests.scoring_engine.helpers import populate_sample_data
from tests.scoring_engine.web.web_test import WebTest


class TestScoreboard(WebTest):

    def test_scoreboard(self):
        populate_sample_data(self.session)
        resp = self.client.get("/scoreboard")
        assert resp.status_code == 200
        assert self.mock_obj.call_args == self.build_args("scoreboard.html")
