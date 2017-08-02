from tests.scoring_engine.web.web_test import WebTest

from scoring_engine.version import version
from scoring_engine.engine.config import config


class TestAbout(WebTest):

    # def setup(self):
    #     super(TestWelcome, self).setup()
    #     self.expected_sponsorship_images = OrderedDict()
    #     self.expected_sponsorship_images['diamond'] = ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg']
    #     self.expected_sponsorship_images['platinum'] = ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg']
    #     self.expected_sponsorship_images['somecustomlevel'] = ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg']
    #     self.expected_sponsorship_images['gold'] = ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg']

    def test_about(self):
        resp = self.client.get('/about')
        assert self.mock_obj.call_args == self.build_args('about.html', version=version, config_about_content=config.web_about_us_page_content)
        assert resp.status_code == 200

    # def test_home_index(self):
    #     resp = self.client.get('/index')
    #     assert self.mock_obj.call_args == self.build_args('welcome.html', sponsorship_images=self.expected_sponsorship_images)
    #     assert resp.status_code == 200
