from unittest.mock import patch

from tests.scoring_engine.web.web_test import WebTest

from scoring_engine.version import version


class TestAbout(WebTest):

    def setup(self):
        super(TestAbout, self).setup()
        self.create_default_user()

    @patch("scoring_engine.version.get_version", return_value="1.0.0")
    def test_about(self, mock_get_version):
        resp = self.client.get("/about")
        assert self.mock_obj.call_args == self.build_args(
            "about.html", version=version, about_content="example content value"
        )
        assert resp.status_code == 200
