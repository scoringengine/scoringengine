import importlib
from flask import render_template as render_template_orig

from flask import session
from flask.testing import FlaskClient as BaseFlaskClient
from flask_wtf.csrf import generate_csrf

from scoring_engine.web import app
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.setting import Setting

from tests.scoring_engine.unit_test import UnitTest
from mock import MagicMock, call


class WebTest(UnitTest):

    def setup(self):
        super(WebTest, self).setup()
        self.app = app
        self.app.test_client_class = FlaskClient
        self.client = self.app.test_client()
        view_name = self.__class__.__name__[4:]
        self.view_module = importlib.import_module('scoring_engine.web.views.' + view_name.lower(), '*')
        self.view_module.render_template = MagicMock()
        self.mock_obj = self.view_module.render_template
        self.mock_obj.side_effect = lambda *args, **kwargs: render_template_orig(*args, **kwargs)

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

    def auth_and_get_path(self, path):
        self.client.login('testuser', 'testpass')
        return self.client.get(path)

    def create_default_user(self):
        team1 = Team(name="Team 1", color="White")
        self.db.save(team1)
        user1 = User(username='testuser', password='testpass', team=team1)
        self.db.save(user1)
        return user1

    def create_default_settings(self):
        setting = Setting(name='about_page_content', value='example content value')
        self.db.save(setting)

    def test_debug(self):
        assert type(self.app.debug) is bool


# Pulled from https://gist.github.com/singingwolfboy/2fca1de64950d5dfed72

# Flask's assumptions about an incoming request don't quite match up with
# what the test client provides in terms of manipulating cookies, and the
# CSRF system depends on cookies working correctly. This little class is a
# fake request that forwards along requests to the test client for setting
# cookies.
class RequestShim(object):
    """
    A fake request that proxies cookie-related methods to a Flask test client.
    """

    def __init__(self, client):
        self.client = client

    def set_cookie(self, key, value='', *args, **kwargs):
        "Set the cookie on the Flask test client."
        server_name = app.config["SERVER_NAME"] or "localhost"
        return self.client.set_cookie(
            server_name, key=key, value=value, *args, **kwargs
        )

    def delete_cookie(self, key, *args, **kwargs):
        "Delete the cookie on the Flask test client."
        server_name = app.config["SERVER_NAME"] or "localhost"
        return self.client.delete_cookie(
            server_name, key=key, *args, **kwargs
        )


# We're going to extend Flask's built-in test client class, so that it knows
# how to look up CSRF tokens for you!
class FlaskClient(BaseFlaskClient):
    @property
    def csrf_token(self):
        # First, we'll wrap our request shim around the test client, so that
        # it will work correctly when Flask asks it to set a cookie.
        request = RequestShim(self)
        # Next, we need to look up any cookies that might already exist on
        # this test client, such as the secure cookie that powers `flask.session`,
        # and make a test request context that has those cookies in it.
        environ_overrides = {}
        self.cookie_jar.inject_wsgi(environ_overrides)
        with app.test_request_context("/login", environ_overrides=environ_overrides):
            # Now, we call Flask-WTF's method of generating a CSRF token...
            csrf_token = generate_csrf()
            # ...which also sets a value in `flask.session`, so we need to
            # ask Flask to save that value to the cookie jar in the test
            # client. This is where we actually use that request shim we made!
            app.save_session(session, request)
            # And finally, return that CSRF token we got from Flask-WTF.
            return csrf_token

    # Feel free to define other methods on this test client. You can even
    # use the `csrf_token` property we just defined, like we're doing here!
    def login(self, username, password):
        return self.post("/login", data={
            "username": username,
            "password": password,
            "csrf_token": self.csrf_token,
        }, follow_redirects=True)

    def logout(self):
        return self.get("/logout", follow_redirects=True)
