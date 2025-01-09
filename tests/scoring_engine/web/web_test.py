import importlib
from flask import render_template as render_template_orig

from scoring_engine.web import create_app
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

from tests.scoring_engine.unit_test import UnitTest
from mock import MagicMock, call


class WebTest(UnitTest):

    def setup(self):
        super(WebTest, self).setup()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False

        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        view_name = self.__class__.__name__[4:]
        self.view_module = importlib.import_module("scoring_engine.web.views." + view_name.lower(), "*")
        self.view_module.render_template = MagicMock()
        self.mock_obj = self.view_module.render_template
        self.mock_obj.side_effect = lambda *args, **kwargs: render_template_orig(*args, **kwargs)

    def teardown(self):
        self.ctx.pop()
        super(WebTest, self).teardown()

    def build_args(self, *args, **kwargs):
        return call(*args, **kwargs)

    def verify_auth_required(self, path):
        resp = self.client.get(path)
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def verify_auth_required_post(self, path):
        resp = self.client.post(path)
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={
                "username": username,
                "password": password,
            },
            follow_redirects=True,
        )

    def logout(self):
        return self.get("/logout", follow_redirects=True)

    def auth_and_get_path(self, path):
        self.client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "testpass",
            },
        )

        return self.client.get(path)

    def create_default_user(self):
        team1 = Team(name="Team 1", color="White")
        self.session.add(team1)
        user1 = User(username="testuser", password="testpass", team=team1)
        self.session.add(user1)
        self.session.commit()
        return user1

    def test_debug(self):
        assert type(self.app.debug) is bool
