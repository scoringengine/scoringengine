from unittest.mock import MagicMock, call

import pytest
from flask import render_template as render_template_orig

import scoring_engine.web.views.services as view_module
from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.helpers import generate_sample_model_tree


class TestServices:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        self.mock_obj = MagicMock(side_effect=render_template_orig)
        view_module.render_template = self.mock_obj
        yield
        view_module.render_template = render_template_orig

    def _create_default_user(self):
        team = Team(name="Team 1", color="White")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        db.session.commit()
        return user

    def _auth_and_get_path(self, path):
        self.client.post("/login", data={"username": "testuser", "password": "testpass"})
        return self.client.get(path)

    def test_auth_required_services(self):
        resp = self.client.get("/services")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_auth_required_service_id(self):
        resp = self.client.get("/service/1")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_normal_services(self):
        user = self._create_default_user()
        service = generate_sample_model_tree("Service", db.session)
        user.team.color = "Blue"
        db.session.add(user.team)
        service.team = user.team
        db.session.add(service)
        db.session.commit()
        resp = self._auth_and_get_path("/services")
        assert resp.status_code == 200
        assert self.mock_obj.call_args == call("services.html")

    def test_unauthorized_services(self):
        user = self._create_default_user()
        service = generate_sample_model_tree("Service", db.session)
        user.team.color = "White"
        db.session.add(user.team)
        service.team = user.team
        db.session.add(service)
        db.session.commit()
        resp = self._auth_and_get_path("/services")
        assert resp.status_code == 302

    def test_normal_service_id(self):
        user = self._create_default_user()
        service = generate_sample_model_tree("Service", db.session)
        user.team.color = "Blue"
        db.session.add(user.team)
        service.team = user.team
        db.session.add(service)
        db.session.commit()
        resp = self._auth_and_get_path("/service/1")
        assert resp.status_code == 200

    def test_unauthorized_service_id(self):
        self._create_default_user()
        resp = self._auth_and_get_path("/service/1")
        assert resp.status_code == 302
