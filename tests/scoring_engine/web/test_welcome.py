from web_test import WebTest
from collections import OrderedDict


class TestWelcome(WebTest):

    def setup(self):
        super(TestWelcome, self).setup()
        self.expected_sponsorship_images = OrderedDict()
        self.expected_sponsorship_images['diamond'] = ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg']
        self.expected_sponsorship_images['platinum'] = ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg']
        self.expected_sponsorship_images['somecustomlevel'] = ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg']
        self.expected_sponsorship_images['gold'] = ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg']

    def test_home(self):
        resp = self.client.get('/')
        assert self.mock_obj.call_args == self.build_args('welcome.html', sponsorship_images=self.expected_sponsorship_images)
        assert resp.status_code == 200

    def test_home_index(self):
        resp = self.client.get('/index')
        assert self.mock_obj.call_args == self.build_args('welcome.html', sponsorship_images=self.expected_sponsorship_images)
        assert resp.status_code == 200
