from unittest.mock import MagicMock, call

import pytest
from flask import render_template as render_template_orig

import scoring_engine.web.views.overview as view_module


class TestOverview:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        self.mock_obj = MagicMock(side_effect=render_template_orig)
        view_module.render_template = self.mock_obj
        yield
        view_module.render_template = render_template_orig

    def test_basic_home(self):
        resp = self.client.get("/overview")
        assert resp.status_code == 200
        assert self.mock_obj.call_args == call("overview.html", teams=[])
