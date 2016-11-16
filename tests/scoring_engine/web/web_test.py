import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.web import app
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from unit_test import UnitTest


class WebTest(UnitTest):

    def setup(self):
        super(WebTest, self).setup()
        self.app = app
        self.client = self.app.test_client()

    def authenticate(self, username, password):
        return self.client.post('/login', data={'username': username, 'password': password})

    def test_debug(self):
        assert self.app.debug is True
