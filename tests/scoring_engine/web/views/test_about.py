from tests.scoring_engine.web.web_test import WebTest

from scoring_engine.version import version


class TestAbout(WebTest):

    def setup(self):
        super(TestAbout, self).setup()
        self.create_default_user()

    def test_about(self):
        resp = self.client.get("/about")
        # TODO - Fix this
        # assert self.mock_obj.call_args == self.build_args(
        #     "about.html", version=version, about_content="example content value"
        # )
        assert resp.status_code == 200
