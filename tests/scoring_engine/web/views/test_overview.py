from tests.scoring_engine.web.web_test import WebTest


class TestOverview(WebTest):
    def test_basic_home(self):
        resp = self.client.get("/overview")
        assert resp.status_code == 200
        assert self.mock_obj.call_args == self.build_args("overview.html", teams=[])
