import mock

from scoring_engine.web.views.auth import LoginForm

from tests.scoring_engine.web.web_test import WebTest


class TestAuth(WebTest):

    def test_login_page_auth_required(self):
        resp = self.client.get('/login')
        assert resp.status_code == 200

    def test_unauthorized(self):
        resp = self.client.get('/unauthorized')
        assert resp.status_code == 200

    def test_auth_required_logout(self):
        self.verify_auth_required('/logout')

    def test_login_logout_whiteteam(self):
        user = self.create_default_user()
        assert user.authenticated is False
        self.auth_and_get_path('/')
        assert user.authenticated is True
        logout_resp = self.client.get('/logout')
        assert user.authenticated is False
        assert logout_resp.status_code == 302
        self.verify_auth_required('/services')

    def test_login_logout_blueteam(self):
        user = self.create_default_user()
        user.team.color = 'Blue'
        self.session.add(user.team)
        self.session.commit()
        assert user.authenticated is False
        self.auth_and_get_path('/')
        assert user.authenticated is True
        logout_resp = self.client.get('/logout')
        assert user.authenticated is False
        assert logout_resp.status_code == 302
        self.verify_auth_required('/services')

    def test_login_logout_redteam(self):
        user = self.create_default_user()
        user.team.color = 'Red'
        self.session.add(user.team)
        self.session.commit()
        assert user.authenticated is False
        self.auth_and_get_path('/')
        assert user.authenticated is True
        logout_resp = self.client.get('/logout')
        assert user.authenticated is False
        assert logout_resp.status_code == 302
        self.verify_auth_required('/services')

    def test_wrong_username_login(self):
        user = self.create_default_user()
        user.username = 'RandomName'
        self.session.add(user)
        self.session.commit()
        self.auth_and_get_path('/')
        assert user.authenticated is False

    def test_wrong_password_login(self):
        user = self.create_default_user()
        user.update_password('randompass')
        self.session.add(user)
        self.session.commit()
        self.auth_and_get_path('/')
        assert user.authenticated is False

    def test_form_errors(self):
        with mock.patch.object(LoginForm, 'errors') as mock_fish:
            mock_fish.__get__ = mock.Mock(return_value='Some error text')
            self.client.get('/login')

    def test_login_twice(self):
        self.create_default_user()
        self.auth_and_get_path('/')
        self.auth_and_get_path('/')
