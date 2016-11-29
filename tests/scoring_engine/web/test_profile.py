from web_test import WebTest


class TestProfile(WebTest):

    def test_home_auth_required(self):
        self.verify_auth_required('/profile')
