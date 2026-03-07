"""Tests for Admin Inject Template Import API endpoint"""

import json
from datetime import datetime, timezone

from scoring_engine.models.inject import Inject, Template
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
import pytest

from scoring_engine.db import db


class TestAdminInjectImportAPI:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

        self.white_team = Team(name="White Team", color="White")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")

        db.session.add_all([self.white_team, self.blue_team1, self.blue_team2, self.red_team])
        db.session.commit()

        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.blue_user = User(username="blueuser", password="testpass", team=self.blue_team1)
        db.session.add_all([self.white_user, self.blue_user])
        db.session.commit()

    def login(self, username):
        return self.client.post(
            "/login",
            data={"username": username, "password": "testpass"},
            follow_redirects=True,
        )

    def _make_template_data(self, **overrides):
        data = {
            "title": "Test Inject",
            "scenario": "Do the thing",
            "deliverable": "A report",
            "start_time": "2026-02-07T09:00:00-05:00",
            "end_time": "2026-02-07T17:00:00-05:00",
            "enabled": True,
            "teams": ["Blue Team 1", "Blue Team 2"],
            "rubric_items": [
                {"title": "Overall Quality", "points": 100},
            ],
        }
        data.update(overrides)
        return data

    # --- Authorization ---

    def test_import_requires_auth(self):
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([self._make_template_data()]),
            content_type="application/json",
        )
        assert resp.status_code == 302

    def test_import_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([self._make_template_data()]),
            content_type="application/json",
        )
        assert resp.status_code == 403

    # --- Create new templates (no id) ---

    def test_import_creates_new_template(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([self._make_template_data()]),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"

        templates = db.session.query(Template).all()
        assert len(templates) == 1
        assert templates[0].title == "Test Inject"

    def test_import_creates_injects_for_matching_teams(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([self._make_template_data()]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        injects = db.session.query(Inject).all()
        assert len(injects) == 2
        team_names = {i.team.name for i in injects}
        assert team_names == {"Blue Team 1", "Blue Team 2"}

    def test_import_multiple_templates(self):
        self.login("whiteuser")
        data = [
            self._make_template_data(title="Inject A"),
            self._make_template_data(title="Inject B"),
        ]
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert db.session.query(Template).count() == 2

    # --- Import with non-existent id falls through to create ---

    def test_import_with_nonexistent_id_creates_template(self):
        """Importing with an id that doesn't exist in the DB should create a new template"""
        self.login("whiteuser")
        data = self._make_template_data(id=9999, title="From Export")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"

        templates = db.session.query(Template).all()
        assert len(templates) == 1
        assert templates[0].title == "From Export"

    # --- Unknown team names are skipped ---

    def test_import_skips_unknown_team_names(self):
        """Team names that don't exist in the DB should be silently skipped"""
        self.login("whiteuser")
        data = self._make_template_data(teams=["Blue Team 1", "Nonexistent Team", "Team0"])
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        injects = db.session.query(Inject).all()
        assert len(injects) == 1
        assert injects[0].team.name == "Blue Team 1"

    def test_import_all_unknown_teams_creates_template_with_no_injects(self):
        """If all teams are unknown, template is created but no injects"""
        self.login("whiteuser")
        data = self._make_template_data(teams=["Team0", "Team1", "Team2"])
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        assert db.session.query(Template).count() == 1
        assert db.session.query(Inject).count() == 0

    # --- Update existing template ---

    def test_import_with_existing_id_updates_template(self):
        """Importing with an id that exists should update the template"""
        self.login("whiteuser")
        template = Template(
            title="Old Title",
            scenario="Old scenario",
            deliverable="Old deliverable",
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
            enabled=True,
        )
        db.session.add(template)
        db.session.commit()
        template_id = template.id

        data = {
            "id": template_id,
            "title": "New Title",
            "scenario": "New scenario",
            "deliverable": "New deliverable",
            "start_time": "2026-02-07T09:00:00-05:00",
            "end_time": "2026-02-07T17:00:00-05:00",
            "enabled": True,
        }
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        db.session.refresh(template)
        assert template.title == "New Title"
        assert template.scenario == "New scenario"

    # --- GET template endpoint guards null teams ---

    def test_get_template_with_null_team_inject(self):
        """GET /api/admin/injects/templates/<id> should not crash if an inject has null team"""
        self.login("whiteuser")
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="-",
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        db.session.add(template)
        db.session.commit()

        # Manually create an inject with null team
        inject = Inject(team=None, template=template, enabled=True)
        db.session.add(inject)
        db.session.commit()

        resp = self.client.get(f"/api/admin/injects/templates/{template.id}")
        assert resp.status_code == 200
        assert resp.json["title"] == "Test"
        assert resp.json["teams"] == []

    # --- Scores endpoint guards null teams ---

    def test_scores_endpoint_with_null_team_inject(self):
        """GET /api/admin/injects/scores should not crash if an inject has null team"""
        self.login("whiteuser")
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="-",
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        db.session.add(template)
        db.session.commit()

        # Create a normal inject and one with null team
        inject_good = Inject(team=self.blue_team1, template=template, enabled=True)
        inject_bad = Inject(team=None, template=template, enabled=True)
        db.session.add_all([inject_good, inject_bad])
        db.session.commit()

        resp = self.client.get("/api/admin/injects/scores")
        assert resp.status_code == 200

    # --- end_time parsing uses correct field ---

    def test_import_end_time_parsed_correctly(self):
        """end_time should use the end_time field, not start_time"""
        self.login("whiteuser")
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="-",
            start_time=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        db.session.add(template)
        db.session.commit()

        data = {
            "id": template.id,
            "start_time": "2026-03-01T09:00:00+00:00",
            "end_time": "2026-03-01T17:00:00+00:00",
            "enabled": True,
        }
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        db.session.refresh(template)
        # end_time should be 17:00, not 09:00 (the start_time)
        assert template.end_time.hour == 17
        assert template.start_time.hour == 9

    # --- Empty / invalid data ---

    def test_import_empty_data_returns_error(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert resp.json["message"] == "Invalid Data"
