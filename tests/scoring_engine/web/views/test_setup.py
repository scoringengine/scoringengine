import tempfile
from pathlib import Path
from mock import patch

from tests.scoring_engine.web.web_test import WebTest


class TestSetup(WebTest):
    def test_redirect_when_no_teams(self):
        resp = self.client.get("/")
        assert resp.status_code == 302
        assert resp.location.endswith("/setup")

    def test_redirect_when_missing_competition(self):
        self.create_default_user()
        with patch(
            "scoring_engine.web.views.welcome.os.path.exists", return_value=False
        ):
            resp = self.client.get("/")
        assert resp.status_code == 302
        assert resp.location.endswith("/setup")

    def test_wizard_creates_competition_yaml(self):
        tmp_dir = tempfile.TemporaryDirectory()
        comp_file = Path(tmp_dir.name) / "competition.yaml"
        with patch(
            "scoring_engine.web.views.setup.competition_file_path",
            return_value=str(comp_file),
        ):
            resp = self.client.post(
                "/setup?step=1",
                data={"username": "admin", "password": "pass"},
            )
            assert resp.status_code == 302
            assert resp.location.endswith("step=2")

            resp = self.client.post(
                "/setup?step=2", data={"num_teams": "1"}
            )
            assert resp.status_code == 302
            assert resp.location.endswith("step=3")

            resp = self.client.post(
                "/setup?step=3",
                data={
                    "service_name": "Web",
                    "check_name": "HTTPCheck",
                    "host": "localhost",
                    "port": "80",
                    "points": "100",
                    "matching_content": "OK",
                    "properties": "useragent=UA\nvhost=example.com\nuri=/",
                    "action": "finish",
                },
            )
            assert resp.status_code == 302
            assert resp.location.endswith("step=4")
            assert comp_file.exists()
        tmp_dir.cleanup()

