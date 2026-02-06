"""Tests for Admin Inject Template Import API endpoint"""
import json
from datetime import datetime, timezone

from scoring_engine.models.inject import Inject, Template
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.unit_test import UnitTest
from scoring_engine.web import create_app
from scoring_engine.db import db


class TestAdminInjectImportAPI(UnitTest):

    def setup_method(self):
        super(TestAdminInjectImportAPI, self).setup_method()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.white_team = Team(name="White Team", color="White")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")

        self.session.add_all(
            [self.white_team, self.blue_team1, self.blue_team2, self.red_team]
        )
        self.session.commit()

        self.white_user = User(
            username="whiteuser", password="pass", team=self.white_team
        )
        self.blue_user = User(
            username="blueuser", password="pass", team=self.blue_team1
        )
        self.session.add_all([self.white_user, self.blue_user])
        self.session.commit()

    def teardown_method(self):
        self.ctx.pop()
        super(TestAdminInjectImportAPI, self).teardown_method()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def _make_template_data(self, **overrides):
        data = {
            "title": "Test Inject",
            "scenario": "Do the thing",
            "deliverable": "A report",
            "score": 100,
            "start_time": "2026-02-07T09:00:00-05:00",
            "end_time": "2026-02-07T17:00:00-05:00",
            "enabled": True,
            "teams": ["Blue Team 1", "Blue Team 2"],
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
        self.login("blueuser", "pass")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([self._make_template_data()]),
            content_type="application/json",
        )
        assert resp.status_code == 403

    # --- Create new templates (no id) ---

    def test_import_creates_new_template(self):
        self.login("whiteuser", "pass")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([self._make_template_data()]),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"

        templates = self.session.query(Template).all()
        assert len(templates) == 1
        assert templates[0].title == "Test Inject"

    def test_import_creates_injects_for_matching_teams(self):
        self.login("whiteuser", "pass")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([self._make_template_data()]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        injects = self.session.query(Inject).all()
        assert len(injects) == 2
        team_names = {i.team.name for i in injects}
        assert team_names == {"Blue Team 1", "Blue Team 2"}

    def test_import_multiple_templates(self):
        self.login("whiteuser", "pass")
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
        assert self.session.query(Template).count() == 2

    # --- Import with non-existent id falls through to create ---

    def test_import_with_nonexistent_id_creates_template(self):
        """Importing with an id that doesn't exist in the DB should create a new template"""
        self.login("whiteuser", "pass")
        data = self._make_template_data(id=9999, title="From Export")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"

        templates = self.session.query(Template).all()
        assert len(templates) == 1
        assert templates[0].title == "From Export"

    def test_import_with_nonexistent_id_creates_injects(self):
        """Injects should still be created for teams when id doesn't match"""
        self.login("whiteuser", "pass")
        data = self._make_template_data(id=9999)
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        injects = self.session.query(Inject).all()
        assert len(injects) == 2
        assert all(i.team is not None for i in injects)

    # --- Unknown team names are skipped ---

    def test_import_skips_unknown_team_names(self):
        """Team names that don't exist in the DB should be silently skipped"""
        self.login("whiteuser", "pass")
        data = self._make_template_data(
            teams=["Blue Team 1", "Nonexistent Team", "Team0"]
        )
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        injects = self.session.query(Inject).all()
        assert len(injects) == 1
        assert injects[0].team.name == "Blue Team 1"

    def test_import_all_unknown_teams_creates_template_with_no_injects(self):
        """If all teams are unknown, template is created but no injects"""
        self.login("whiteuser", "pass")
        data = self._make_template_data(teams=["Team0", "Team1", "Team2"])
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps([data]),
            content_type="application/json",
        )
        assert resp.status_code == 200

        assert self.session.query(Template).count() == 1
        assert self.session.query(Inject).count() == 0

    # --- Update existing template ---

    def test_import_with_existing_id_updates_template(self):
        """Importing with an id that exists should update the template"""
        self.login("whiteuser", "pass")
        template = Template(
            title="Old Title",
            scenario="Old scenario",
            deliverable="Old deliverable",
            score=50,
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
            enabled=True,
        )
        self.session.add(template)
        self.session.commit()
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

        self.session.refresh(template)
        assert template.title == "New Title"
        assert template.scenario == "New scenario"

    # --- GET template endpoint guards null teams ---

    def test_get_template_with_null_team_inject(self):
        """GET /api/admin/injects/templates/<id> should not crash if an inject has null team"""
        self.login("whiteuser", "pass")
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="-",
            score=1,
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        self.session.add(template)
        self.session.commit()

        # Manually create an inject with null team
        inject = Inject(team=None, template=template, enabled=True)
        self.session.add(inject)
        self.session.commit()

        resp = self.client.get(f"/api/admin/injects/templates/{template.id}")
        assert resp.status_code == 200
        assert resp.json["title"] == "Test"
        assert resp.json["teams"] == []

    # --- Scores endpoint guards null teams ---

    def test_scores_endpoint_with_null_team_inject(self):
        """GET /api/admin/injects/scores should not crash if an inject has null team"""
        self.login("whiteuser", "pass")
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="-",
            score=1,
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        self.session.add(template)
        self.session.commit()

        # Create a normal inject and one with null team
        inject_good = Inject(team=self.blue_team1, template=template, enabled=True)
        inject_bad = Inject(team=None, template=template, enabled=True)
        self.session.add_all([inject_good, inject_bad])
        self.session.commit()

        resp = self.client.get("/api/admin/injects/scores")
        assert resp.status_code == 200

    # --- end_time parsing uses correct field ---

    def test_import_end_time_parsed_correctly(self):
        """end_time should use the end_time field, not start_time"""
        self.login("whiteuser", "pass")
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="-",
            score=1,
            start_time=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        self.session.add(template)
        self.session.commit()

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

        self.session.refresh(template)
        # end_time should be 17:00, not 09:00 (the start_time)
        assert template.end_time.hour == 17
        assert template.start_time.hour == 9

    # --- Empty / invalid data ---

    def test_import_empty_data_returns_error(self):
        self.login("whiteuser", "pass")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert resp.json["message"] == "Invalid Data"
