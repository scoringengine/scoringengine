from web_test import WebTest


class TestServices(WebTest):

    def test_auth_required_services(self):
        self.verify_auth_required('/services')

    def test_auth_required_service_id(self):
        self.verify_auth_required('/service/1')
