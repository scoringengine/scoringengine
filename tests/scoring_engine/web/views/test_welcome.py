from unittest.mock import MagicMock, call

import pytest
from flask import render_template as render_template_orig

import scoring_engine.web.views.welcome as view_module
from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestWelcome:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        self.welcome_content = "example welcome content <br>here"

        team = Team(name="Team 1", color="White")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        db.session.commit()

        self.mock_obj = MagicMock(side_effect=render_template_orig)
        view_module.render_template = self.mock_obj
        yield
        view_module.render_template = render_template_orig

    def test_home(self):
        resp = self.client.get("/")
        assert self.mock_obj.call_args == call("welcome.html", welcome_content=self.welcome_content)
        assert resp.status_code == 200

    def test_home_index(self):
        resp = self.client.get("/index")
        assert self.mock_obj.call_args == call("welcome.html", welcome_content=self.welcome_content)
        assert resp.status_code == 200
