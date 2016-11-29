import importlib
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.web import app
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from unit_test import UnitTest
from mock import MagicMock, call

from flask import render_template as render_template_backup


class WebTest(UnitTest):

    def setup(self):
        super(WebTest, self).setup()
        self.app = app
        self.client = self.app.test_client()
        self.view_module = importlib.import_module('scoring_engine.web.views.' + self.view_name, '*')
        self.view_module.render_template = MagicMock()
        self.mock_obj = self.view_module.render_template
        self.mock_obj.side_effect = lambda *args, **kwargs: render_template_backup(*args, **kwargs)

    def build_args(self, *args, **kwargs):
        return call(*args, **kwargs)

    def verify_auth_required(self, path):
        resp = self.client.get(path)
        assert resp.status_code == 302
        assert '/login?' in resp.location

    def verify_auth_required_post(self, path):
        resp = self.client.post(path)
        assert resp.status_code == 302
        assert '/login?' in resp.location

    def test_debug(self):
        assert self.app.debug is True
