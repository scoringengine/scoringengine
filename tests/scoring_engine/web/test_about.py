from tests.scoring_engine.web.web_test import WebTest

from scoring_engine.version import version
from scoring_engine.engine.config import config


class TestAbout(WebTest):

    def test_about(self):
        resp = self.client.get('/about')
        assert self.mock_obj.call_args == self.build_args('about.html', version=version, config_about_content=config.web_about_us_page_content)
        assert resp.status_code == 200
