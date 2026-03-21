"""Extended tests for Admin API endpoints not covered by test_admin_api.py."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.inject import Inject, InjectComment, InjectRubricScore, RubricItem, Template
from scoring_engine.models.property import Property
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestAdminAPIExtended:
    """Tests for admin API endpoints not covered by test_admin_api.py."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.white_team = three_teams["white_team"]
        self.blue_team = three_teams["blue_team"]
        self.red_team = three_teams["red_team"]
        self.white_user = three_teams["white_user"]
        self.blue_user = three_teams["blue_user"]
        self.red_user = three_teams["red_user"]

    def login(self, username, password="testpass"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def _make_service(self, **kwargs):
        defaults = dict(name="TestSvc", check_name="ICMP IPv4 Check", host="10.0.0.1", team=self.blue_team)
        defaults.update(kwargs)
        svc = Service(**defaults)
        db.session.add(svc)
        db.session.flush()
        return svc

    def _make_template(self, **kwargs):
        defaults = dict(
            title="Test Inject",
            scenario="Test scenario",
            deliverable="Test deliverable",
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        defaults.update(kwargs)
        t = Template(**defaults)
        db.session.add(t)
        db.session.flush()
        return t

    # -----------------------------------------------------------------------
    # POST /api/admin/update_host
    # -----------------------------------------------------------------------
    def test_update_host_requires_auth(self):
        resp = self.client.post("/api/admin/update_host")
        assert resp.status_code == 302

    def test_update_host_requires_white_team(self):
        svc = self._make_service()
        db.session.commit()
        self.login("blueuser")
        resp = self.client.post("/api/admin/update_host", data={"pk": svc.id, "name": "host", "value": "10.0.0.2"})
        assert resp.json["error"] == "Incorrect permissions"

    def test_update_host_success(self):
        svc = self._make_service()
        db.session.commit()
        self.login("whiteuser")
        with patch("scoring_engine.web.views.api.admin.update_overview_data"), \
             patch("scoring_engine.web.views.api.admin.update_services_data"), \
             patch("scoring_engine.web.views.api.admin.update_service_data"):
            resp = self.client.post("/api/admin/update_host", data={"pk": svc.id, "name": "host", "value": "10.0.0.2"})
        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Service Information"
        db.session.refresh(svc)
        assert svc.host == "10.0.0.2"

    # -----------------------------------------------------------------------
    # POST /api/admin/update_port
    # -----------------------------------------------------------------------
    def test_update_port_requires_auth(self):
        resp = self.client.post("/api/admin/update_port")
        assert resp.status_code == 302

    def test_update_port_requires_white_team(self):
        svc = self._make_service()
        db.session.commit()
        self.login("blueuser")
        resp = self.client.post("/api/admin/update_port", data={"pk": svc.id, "name": "port", "value": "8080"})
        assert resp.json["error"] == "Incorrect permissions"

    def test_update_port_success(self):
        svc = self._make_service()
        db.session.commit()
        self.login("whiteuser")
        with patch("scoring_engine.web.views.api.admin.update_overview_data"), \
             patch("scoring_engine.web.views.api.admin.update_services_data"), \
             patch("scoring_engine.web.views.api.admin.update_service_data"):
            resp = self.client.post("/api/admin/update_port", data={"pk": svc.id, "name": "port", "value": "8080"})
        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Service Information"
        db.session.refresh(svc)
        assert svc.port == 8080

    # -----------------------------------------------------------------------
    # POST /api/admin/update_worker_queue
    # -----------------------------------------------------------------------
    def test_update_worker_queue_requires_auth(self):
        resp = self.client.post("/api/admin/update_worker_queue")
        assert resp.status_code == 302

    def test_update_worker_queue_requires_white_team(self):
        svc = self._make_service()
        db.session.commit()
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/update_worker_queue", data={"pk": svc.id, "name": "worker_queue", "value": "worker2"}
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_update_worker_queue_success(self):
        svc = self._make_service()
        db.session.commit()
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_worker_queue", data={"pk": svc.id, "name": "worker_queue", "value": "worker2"}
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Service Information"
        db.session.refresh(svc)
        assert svc.worker_queue == "worker2"

    # -----------------------------------------------------------------------
    # POST /api/admin/update_points
    # -----------------------------------------------------------------------
    def test_update_points_requires_auth(self):
        resp = self.client.post("/api/admin/update_points")
        assert resp.status_code == 302

    def test_update_points_requires_white_team(self):
        svc = self._make_service()
        db.session.commit()
        self.login("blueuser")
        resp = self.client.post("/api/admin/update_points", data={"pk": svc.id, "name": "points", "value": "200"})
        assert resp.json["error"] == "Incorrect permissions"

    def test_update_points_success(self):
        svc = self._make_service()
        db.session.commit()
        self.login("whiteuser")
        resp = self.client.post("/api/admin/update_points", data={"pk": svc.id, "name": "points", "value": "200"})
        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Service Information"
        db.session.refresh(svc)
        assert svc.points == 200

    # -----------------------------------------------------------------------
    # POST /api/admin/update_about_page_content
    # -----------------------------------------------------------------------
    def test_update_about_page_content_requires_auth(self):
        resp = self.client.post("/api/admin/update_about_page_content")
        assert resp.status_code == 302

    def test_update_about_page_content_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/update_about_page_content", data={"about_page_content": "new content"}
        )
        assert resp.status_code == 403

    def test_update_about_page_content_success(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_about_page_content",
            data={"about_page_content": "Updated about page"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        setting = Setting.get_setting("about_page_content")
        assert setting.value == "Updated about page"

    def test_update_about_page_content_missing_field(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/update_about_page_content", data={}, follow_redirects=True)
        assert resp.status_code == 200  # Redirects with flash error

    # -----------------------------------------------------------------------
    # POST /api/admin/update_welcome_page_content
    # -----------------------------------------------------------------------
    def test_update_welcome_page_content_requires_auth(self):
        resp = self.client.post("/api/admin/update_welcome_page_content")
        assert resp.status_code == 302

    def test_update_welcome_page_content_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/update_welcome_page_content", data={"welcome_page_content": "new"}
        )
        assert resp.status_code == 403

    def test_update_welcome_page_content_success(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_welcome_page_content",
            data={"welcome_page_content": "New welcome content"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        setting = Setting.get_setting("welcome_page_content")
        assert setting.value == "New welcome content"

    def test_update_welcome_page_content_missing_field(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/update_welcome_page_content", data={}, follow_redirects=True)
        assert resp.status_code == 200  # Redirects with flash error

    # -----------------------------------------------------------------------
    # POST /api/admin/update_target_round_time
    # -----------------------------------------------------------------------
    def test_update_target_round_time_requires_auth(self):
        resp = self.client.post("/api/admin/update_target_round_time")
        assert resp.status_code == 302

    def test_update_target_round_time_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/update_target_round_time", data={"target_round_time": "120"}
        )
        assert resp.status_code == 403

    def test_update_target_round_time_success(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_target_round_time",
            data={"target_round_time": "120"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        setting = Setting.get_setting("target_round_time")
        assert str(setting.value) == "120"

    def test_update_target_round_time_non_integer(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_target_round_time",
            data={"target_round_time": "abc"},
            follow_redirects=True,
        )
        assert resp.status_code == 200  # Redirect with flash error

    def test_update_target_round_time_missing_field(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/update_target_round_time", data={}, follow_redirects=True)
        assert resp.status_code == 200

    # -----------------------------------------------------------------------
    # POST /api/admin/update_worker_refresh_time
    # -----------------------------------------------------------------------
    def test_update_worker_refresh_time_requires_auth(self):
        resp = self.client.post("/api/admin/update_worker_refresh_time")
        assert resp.status_code == 302

    def test_update_worker_refresh_time_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/update_worker_refresh_time", data={"worker_refresh_time": "45"}
        )
        assert resp.status_code == 403

    def test_update_worker_refresh_time_success(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_worker_refresh_time",
            data={"worker_refresh_time": "45"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        setting = Setting.get_setting("worker_refresh_time")
        assert str(setting.value) == "45"

    def test_update_worker_refresh_time_non_integer(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_worker_refresh_time",
            data={"worker_refresh_time": "abc"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_update_worker_refresh_time_missing_field(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/update_worker_refresh_time", data={}, follow_redirects=True)
        assert resp.status_code == 200

    # -----------------------------------------------------------------------
    # Blue team permission toggle endpoints
    # -----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "endpoint,setting_name",
        [
            ("/api/admin/update_blueteam_edit_hostname", "blue_team_update_hostname"),
            ("/api/admin/update_blueteam_edit_port", "blue_team_update_port"),
            ("/api/admin/update_blueteam_edit_account_usernames", "blue_team_update_account_usernames"),
            ("/api/admin/update_blueteam_edit_account_passwords", "blue_team_update_account_passwords"),
            ("/api/admin/update_blueteam_view_check_output", "blue_team_view_check_output"),
        ],
    )
    def test_blueteam_toggle_requires_auth(self, endpoint, setting_name):
        resp = self.client.post(endpoint)
        assert resp.status_code == 302

    @pytest.mark.parametrize(
        "endpoint,setting_name",
        [
            ("/api/admin/update_blueteam_edit_hostname", "blue_team_update_hostname"),
            ("/api/admin/update_blueteam_edit_port", "blue_team_update_port"),
            ("/api/admin/update_blueteam_edit_account_usernames", "blue_team_update_account_usernames"),
            ("/api/admin/update_blueteam_edit_account_passwords", "blue_team_update_account_passwords"),
            ("/api/admin/update_blueteam_view_check_output", "blue_team_view_check_output"),
        ],
    )
    def test_blueteam_toggle_requires_white_team(self, endpoint, setting_name):
        self.login("blueuser")
        resp = self.client.post(endpoint)
        assert resp.status_code == 403

    @pytest.mark.parametrize(
        "endpoint,setting_name",
        [
            ("/api/admin/update_blueteam_edit_hostname", "blue_team_update_hostname"),
            ("/api/admin/update_blueteam_edit_port", "blue_team_update_port"),
            ("/api/admin/update_blueteam_edit_account_usernames", "blue_team_update_account_usernames"),
            ("/api/admin/update_blueteam_edit_account_passwords", "blue_team_update_account_passwords"),
            ("/api/admin/update_blueteam_view_check_output", "blue_team_view_check_output"),
        ],
    )
    def test_blueteam_toggle_true_to_false(self, endpoint, setting_name):
        """Default is True; toggling should set to False."""
        self.login("whiteuser")
        setting = Setting.get_setting(setting_name)
        assert setting.value is True
        resp = self.client.post(endpoint, follow_redirects=True)
        assert resp.status_code == 200
        Setting.clear_cache(setting_name)
        setting = Setting.get_setting(setting_name)
        assert setting.value is False

    @pytest.mark.parametrize(
        "endpoint,setting_name",
        [
            ("/api/admin/update_blueteam_edit_hostname", "blue_team_update_hostname"),
            ("/api/admin/update_blueteam_edit_port", "blue_team_update_port"),
            ("/api/admin/update_blueteam_edit_account_usernames", "blue_team_update_account_usernames"),
            ("/api/admin/update_blueteam_edit_account_passwords", "blue_team_update_account_passwords"),
            ("/api/admin/update_blueteam_view_check_output", "blue_team_view_check_output"),
        ],
    )
    def test_blueteam_toggle_false_to_true(self, endpoint, setting_name):
        """Set to False first, then toggle should set back to True."""
        setting = Setting.get_setting(setting_name)
        setting.value = False
        db.session.commit()
        Setting.clear_cache(setting_name)

        self.login("whiteuser")
        resp = self.client.post(endpoint, follow_redirects=True)
        assert resp.status_code == 200
        Setting.clear_cache(setting_name)
        setting = Setting.get_setting(setting_name)
        assert setting.value is True

    # -----------------------------------------------------------------------
    # POST /api/admin/update_anonymize_team_names
    # -----------------------------------------------------------------------
    def test_update_anonymize_team_names_requires_auth(self):
        resp = self.client.post("/api/admin/update_anonymize_team_names")
        assert resp.status_code == 302

    def test_update_anonymize_team_names_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post("/api/admin/update_anonymize_team_names")
        assert resp.status_code == 403

    def test_update_anonymize_team_names_toggle_on(self):
        """Default is False; toggling should set to True."""
        self.login("whiteuser")
        setting = Setting.get_setting("anonymize_team_names")
        assert setting.value is False
        resp = self.client.post("/api/admin/update_anonymize_team_names", follow_redirects=True)
        assert resp.status_code == 200
        Setting.clear_cache("anonymize_team_names")
        setting = Setting.get_setting("anonymize_team_names")
        assert setting.value is True

    def test_update_anonymize_team_names_toggle_off(self):
        """Set to True first, toggle should set back to False."""
        setting = Setting.get_setting("anonymize_team_names")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")

        self.login("whiteuser")
        resp = self.client.post("/api/admin/update_anonymize_team_names", follow_redirects=True)
        assert resp.status_code == 200
        Setting.clear_cache("anonymize_team_names")
        setting = Setting.get_setting("anonymize_team_names")
        assert setting.value is False

    # -----------------------------------------------------------------------
    # GET /api/admin/check/<check_id>/full_output
    # -----------------------------------------------------------------------
    def test_check_full_output_requires_auth(self):
        resp = self.client.get("/api/admin/check/1/full_output")
        assert resp.status_code == 302

    def test_check_full_output_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/check/1/full_output")
        assert resp.status_code == 403

    def test_check_full_output_not_found(self):
        self.login("whiteuser")
        resp = self.client.get("/api/admin/check/99999/full_output")
        assert resp.status_code == 404

    def test_check_full_output_from_db(self):
        svc = self._make_service()
        rnd = Round(number=1)
        db.session.add(rnd)
        db.session.flush()
        check = Check(service=svc, round=rnd, result=True, output="check output text")
        db.session.add(check)
        db.session.commit()

        self.login("whiteuser")
        with patch("scoring_engine.web.views.api.admin.os.path.isfile", return_value=False):
            resp = self.client.get(f"/api/admin/check/{check.id}/full_output")
        assert resp.status_code == 200
        assert b"check output text" in resp.data

    def test_check_full_output_from_file(self):
        svc = self._make_service()
        rnd = Round(number=1)
        db.session.add(rnd)
        db.session.flush()
        check = Check(service=svc, round=rnd, result=True, output="db fallback")
        db.session.add(check)
        db.session.commit()

        self.login("whiteuser")
        mock_open = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value="file output")))
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        with patch("scoring_engine.web.views.api.admin.os.path.isfile", return_value=True), \
             patch("builtins.open", mock_open):
            resp = self.client.get(f"/api/admin/check/{check.id}/full_output")
        assert resp.status_code == 200
        assert b"file output" in resp.data

    # -----------------------------------------------------------------------
    # GET /api/admin/injects/templates/<template_id>
    # -----------------------------------------------------------------------
    def test_get_template_by_id_requires_auth(self):
        resp = self.client.get("/api/admin/injects/templates/1")
        assert resp.status_code == 302

    def test_get_template_by_id_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/injects/templates/1")
        assert resp.status_code == 403

    def test_get_template_by_id_success(self):
        template = self._make_template()
        ri = RubricItem(title="Quality", points=50, template=template, order=0)
        db.session.add(ri)
        inject = Inject(team=self.blue_team, template=template)
        db.session.add(inject)
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.get(f"/api/admin/injects/templates/{template.id}")
        assert resp.status_code == 200
        data = resp.json
        assert data["title"] == "Test Inject"
        assert len(data["rubric_items"]) == 1
        assert data["rubric_items"][0]["title"] == "Quality"
        assert "Blue Team" in data["teams"]

    # -----------------------------------------------------------------------
    # PUT /api/admin/injects/templates/<template_id>
    # -----------------------------------------------------------------------
    def test_put_template_requires_auth(self):
        resp = self.client.put("/api/admin/injects/templates/1", json={})
        assert resp.status_code == 302

    def test_put_template_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.put("/api/admin/injects/templates/1", json={})
        assert resp.status_code == 403

    def test_put_template_not_found(self):
        self.login("whiteuser")
        resp = self.client.put("/api/admin/injects/templates/99999", json={"title": "X"})
        assert resp.status_code == 400
        assert resp.json["message"] == "Template not found"

    def test_put_template_update_fields(self):
        template = self._make_template()
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.put(
            f"/api/admin/injects/templates/{template.id}",
            json={
                "title": "Updated Title",
                "scenario": "Updated scenario",
                "deliverable": "Updated deliverable",
                "status": "Disabled",
            },
        )
        assert resp.status_code == 200
        db.session.refresh(template)
        assert template.title == "Updated Title"
        assert template.scenario == "Updated scenario"
        assert template.enabled is False

    def test_put_template_update_rubric_items(self):
        template = self._make_template()
        ri = RubricItem(title="Old Item", points=50, template=template, order=0)
        db.session.add(ri)
        db.session.commit()
        ri_id = ri.id

        self.login("whiteuser")
        resp = self.client.put(
            f"/api/admin/injects/templates/{template.id}",
            json={
                "rubric_items": [
                    {"id": ri_id, "title": "Updated Item", "points": 75, "order": 0},
                    {"title": "New Item", "points": 25, "order": 1},
                ],
            },
        )
        assert resp.status_code == 200
        db.session.refresh(template)
        assert len(template.rubric_items) == 2

    def test_put_template_selected_teams(self):
        template = self._make_template()
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.put(
            f"/api/admin/injects/templates/{template.id}",
            json={"selectedTeams": ["Blue Team"]},
        )
        assert resp.status_code == 200
        inject = db.session.query(Inject).filter_by(template_id=template.id).first()
        assert inject is not None
        assert inject.team.name == "Blue Team"

    def test_put_template_unselected_teams(self):
        template = self._make_template()
        inject = Inject(team=self.blue_team, template=template)
        db.session.add(inject)
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.put(
            f"/api/admin/injects/templates/{template.id}",
            json={"unselectedTeams": ["Blue Team"]},
        )
        assert resp.status_code == 200
        db.session.refresh(inject)
        assert inject.enabled is False

    # -----------------------------------------------------------------------
    # DELETE /api/admin/injects/templates/<template_id>
    # -----------------------------------------------------------------------
    def test_delete_template_requires_auth(self):
        resp = self.client.delete("/api/admin/injects/templates/1")
        assert resp.status_code == 302

    def test_delete_template_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.delete("/api/admin/injects/templates/1")
        assert resp.status_code == 403

    def test_delete_template_not_found(self):
        self.login("whiteuser")
        resp = self.client.delete("/api/admin/injects/templates/99999")
        assert resp.status_code == 400

    def test_delete_template_success(self):
        template = self._make_template()
        db.session.commit()
        tid = template.id

        self.login("whiteuser")
        resp = self.client.delete(f"/api/admin/injects/templates/{tid}")
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"
        assert db.session.get(Template, tid) is None

    # -----------------------------------------------------------------------
    # GET /api/admin/injects/templates (list all)
    # -----------------------------------------------------------------------
    def test_list_templates_requires_auth(self):
        resp = self.client.get("/api/admin/injects/templates")
        assert resp.status_code == 302

    def test_list_templates_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/injects/templates")
        assert resp.status_code == 403

    def test_list_templates_success(self):
        t1 = self._make_template(title="Inject A")
        t2 = self._make_template(title="Inject B")
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.get("/api/admin/injects/templates")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json["data"]]
        assert "Inject A" in titles
        assert "Inject B" in titles

    # -----------------------------------------------------------------------
    # POST /api/admin/inject/<inject_id>/grade
    # -----------------------------------------------------------------------
    def test_grade_inject_requires_auth(self):
        resp = self.client.post("/api/admin/inject/1/grade", json={})
        assert resp.status_code == 302

    def test_grade_inject_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post("/api/admin/inject/1/grade", json={"rubric_scores": [{"rubric_item_id": 1, "score": 5}]})
        assert resp.status_code == 403

    def test_grade_inject_missing_scores(self):
        self.login("whiteuser")
        template = self._make_template()
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Submitted"
        db.session.add(inject)
        db.session.commit()

        resp = self.client.post(f"/api/admin/inject/{inject.id}/grade", json={"rubric_scores": []})
        assert resp.status_code == 400
        assert resp.json["status"] == "Invalid Score Provided"

    def test_grade_inject_invalid_inject_id(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/inject/99999/grade",
            json={"rubric_scores": [{"rubric_item_id": 1, "score": 5}]},
        )
        assert resp.status_code == 400
        assert resp.json["status"] == "Invalid Inject ID"

    def test_grade_inject_invalid_rubric_item(self):
        self.login("whiteuser")
        template = self._make_template()
        ri = RubricItem(title="Quality", points=100, template=template, order=0)
        db.session.add(ri)
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Submitted"
        db.session.add(inject)
        db.session.commit()

        resp = self.client.post(
            f"/api/admin/inject/{inject.id}/grade",
            json={"rubric_scores": [{"rubric_item_id": 99999, "score": 50}]},
        )
        assert resp.status_code == 400
        assert resp.json["status"] == "Invalid rubric item ID"

    def test_grade_inject_score_exceeds_max(self):
        self.login("whiteuser")
        template = self._make_template()
        ri = RubricItem(title="Quality", points=100, template=template, order=0)
        db.session.add(ri)
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Submitted"
        db.session.add(inject)
        db.session.commit()

        resp = self.client.post(
            f"/api/admin/inject/{inject.id}/grade",
            json={"rubric_scores": [{"rubric_item_id": ri.id, "score": 150}]},
        )
        assert resp.status_code == 400
        assert resp.json["status"] == "Score exceeds rubric item max"

    def test_grade_inject_success(self):
        self.login("whiteuser")
        template = self._make_template()
        ri = RubricItem(title="Quality", points=100, template=template, order=0)
        db.session.add(ri)
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Submitted"
        db.session.add(inject)
        db.session.commit()

        with patch("scoring_engine.web.views.api.admin.update_inject_data"), \
             patch("scoring_engine.web.views.api.admin.update_inject_comments"), \
             patch("scoring_engine.web.views.api.admin.update_scoreboard_data"), \
             patch("scoring_engine.web.views.api.admin.notify_inject_graded"):
            resp = self.client.post(
                f"/api/admin/inject/{inject.id}/grade",
                json={"rubric_scores": [{"rubric_item_id": ri.id, "score": 80}]},
            )
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"
        db.session.refresh(inject)
        assert inject.status == "Graded"
        assert inject.graded is not None
        assert inject.score == 80

    # -----------------------------------------------------------------------
    # POST /api/admin/inject/<inject_id>/request-revision
    # -----------------------------------------------------------------------
    def test_request_revision_requires_auth(self):
        resp = self.client.post("/api/admin/inject/1/request-revision", json={})
        assert resp.status_code == 302

    def test_request_revision_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post("/api/admin/inject/1/request-revision", json={})
        assert resp.status_code == 403

    def test_request_revision_invalid_inject(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/inject/99999/request-revision", json={})
        assert resp.status_code == 400
        assert resp.json["status"] == "Invalid Inject ID"

    def test_request_revision_wrong_status(self):
        self.login("whiteuser")
        template = self._make_template()
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Draft"
        db.session.add(inject)
        db.session.commit()

        resp = self.client.post(f"/api/admin/inject/{inject.id}/request-revision", json={})
        assert resp.status_code == 400
        assert resp.json["status"] == "Inject is not in a submittable state"

    def test_request_revision_success(self):
        self.login("whiteuser")
        template = self._make_template()
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Submitted"
        db.session.add(inject)
        db.session.commit()

        with patch("scoring_engine.web.views.api.admin.update_inject_data"), \
             patch("scoring_engine.web.views.api.admin.update_inject_comments"), \
             patch("scoring_engine.web.views.api.admin.notify_revision_requested"):
            resp = self.client.post(
                f"/api/admin/inject/{inject.id}/request-revision",
                json={"reason": "Please fix the formatting"},
            )
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"
        db.session.refresh(inject)
        assert inject.status == "Revision Requested"

    def test_request_revision_default_reason(self):
        self.login("whiteuser")
        template = self._make_template()
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Submitted"
        db.session.add(inject)
        db.session.commit()

        with patch("scoring_engine.web.views.api.admin.update_inject_data"), \
             patch("scoring_engine.web.views.api.admin.update_inject_comments"), \
             patch("scoring_engine.web.views.api.admin.notify_revision_requested"):
            resp = self.client.post(f"/api/admin/inject/{inject.id}/request-revision", json={})
        assert resp.status_code == 200
        comments = db.session.query(InjectComment).filter_by(inject_id=inject.id).all()
        assert any("Revision requested by grader" in c.content for c in comments)

    # -----------------------------------------------------------------------
    # GET /api/admin/injects/template/<template_id>/submissions
    # -----------------------------------------------------------------------
    def test_template_submissions_requires_auth(self):
        resp = self.client.get("/api/admin/injects/template/1/submissions")
        assert resp.status_code == 302

    def test_template_submissions_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/injects/template/1/submissions")
        assert resp.status_code == 403

    def test_template_submissions_not_found(self):
        self.login("whiteuser")
        resp = self.client.get("/api/admin/injects/template/99999/submissions")
        assert resp.status_code == 404

    def test_template_submissions_success(self):
        template = self._make_template()
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Submitted"
        inject.submitted = datetime.now(timezone.utc)
        db.session.add(inject)
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.get(f"/api/admin/injects/template/{template.id}/submissions")
        assert resp.status_code == 200
        data = resp.json["data"]
        assert len(data) == 1
        assert data[0]["team"] == "Blue Team"
        assert data[0]["status"] == "Submitted"

    # -----------------------------------------------------------------------
    # POST /api/admin/injects/templates (create new)
    # -----------------------------------------------------------------------
    def test_create_template_requires_auth(self):
        resp = self.client.post("/api/admin/injects/templates", json={})
        assert resp.status_code == 302

    def test_create_template_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post("/api/admin/injects/templates", json={})
        assert resp.status_code == 403

    def test_create_template_missing_data(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/injects/templates", json={"title": "Only title"})
        assert resp.status_code == 400
        assert resp.json["message"] == "Missing Data"

    def test_create_template_success(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates",
            json={
                "title": "New Inject",
                "scenario": "Do something",
                "deliverable": "A report",
                "start_time": "2026-01-01T00:00:00-05:00",
                "end_time": "2026-12-31T23:59:59-05:00",
                "rubric_items": [
                    {"title": "Quality", "points": 50},
                    {"title": "Completeness", "points": 50, "description": "Was it complete?"},
                ],
            },
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"
        template = db.session.query(Template).filter_by(title="New Inject").first()
        assert template is not None
        assert len(template.rubric_items) == 2

    def test_create_template_with_teams(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates",
            json={
                "title": "Team Inject",
                "scenario": "Scenario",
                "deliverable": "Deliverable",
                "start_time": "2026-01-01T00:00:00-05:00",
                "end_time": "2026-12-31T23:59:59-05:00",
                "selectedTeams": ["Blue Team"],
            },
        )
        assert resp.status_code == 200
        template = db.session.query(Template).filter_by(title="Team Inject").first()
        inject = db.session.query(Inject).filter_by(template_id=template.id).first()
        assert inject is not None
        assert inject.team.name == "Blue Team"

    def test_create_template_with_status_enabled(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates",
            json={
                "title": "Enabled Inject",
                "scenario": "Scenario",
                "deliverable": "Deliverable",
                "start_time": "2026-01-01T00:00:00-05:00",
                "end_time": "2026-12-31T23:59:59-05:00",
                "status": "Enabled",
            },
        )
        assert resp.status_code == 200
        template = db.session.query(Template).filter_by(title="Enabled Inject").first()
        assert template.enabled is True

    # -----------------------------------------------------------------------
    # POST /api/admin/injects/templates/import
    # -----------------------------------------------------------------------
    def test_import_templates_requires_auth(self):
        resp = self.client.post("/api/admin/injects/templates/import", json=[])
        assert resp.status_code == 302

    def test_import_templates_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post("/api/admin/injects/templates/import", json=[])
        assert resp.status_code == 403

    def test_import_templates_empty_data(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_templates_create_new(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            json=[
                {
                    "title": "Imported Inject",
                    "scenario": "Import scenario",
                    "deliverable": "Import deliverable",
                    "start_time": "2026-01-01T00:00:00-05:00",
                    "end_time": "2026-12-31T23:59:59-05:00",
                    "enabled": True,
                    "teams": ["Blue Team"],
                    "rubric_items": [{"title": "Quality", "points": 100}],
                }
            ],
        )
        assert resp.status_code == 200
        template = db.session.query(Template).filter_by(title="Imported Inject").first()
        assert template is not None
        assert len(template.rubric_items) == 1

    def test_import_templates_update_existing(self):
        template = self._make_template(title="Existing")
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            json=[
                {
                    "id": template.id,
                    "title": "Updated Existing",
                    "scenario": "Updated scenario",
                    "deliverable": "Updated deliverable",
                    "start_time": "2026-06-01T00:00:00-05:00",
                    "end_time": "2026-12-31T23:59:59-05:00",
                    "enabled": True,
                    "teams": [],
                }
            ],
        )
        assert resp.status_code == 200
        db.session.refresh(template)
        assert template.title == "Updated Existing"

    def test_import_templates_nonexistent_id_creates_new(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            json=[
                {
                    "id": 99999,
                    "title": "FallThrough",
                    "scenario": "Scenario",
                    "deliverable": "Deliverable",
                    "start_time": "2026-01-01T00:00:00-05:00",
                    "end_time": "2026-12-31T23:59:59-05:00",
                    "enabled": True,
                    "teams": [],
                }
            ],
        )
        assert resp.status_code == 200
        template = db.session.query(Template).filter_by(title="FallThrough").first()
        assert template is not None

    def test_import_templates_with_score_fallback(self):
        """Test backward compat: if 'score' exists but no rubric_items, creates default rubric item."""
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/injects/templates/import",
            json=[
                {
                    "title": "Legacy Inject",
                    "scenario": "Scenario",
                    "deliverable": "Deliverable",
                    "start_time": "2026-01-01T00:00:00-05:00",
                    "end_time": "2026-12-31T23:59:59-05:00",
                    "enabled": True,
                    "teams": [],
                    "score": 200,
                }
            ],
        )
        assert resp.status_code == 200
        template = db.session.query(Template).filter_by(title="Legacy Inject").first()
        assert template is not None
        assert len(template.rubric_items) == 1
        assert template.rubric_items[0].title == "Overall Quality"
        assert template.rubric_items[0].points == 200

    # -----------------------------------------------------------------------
    # GET /api/admin/injects/scores
    # -----------------------------------------------------------------------
    def test_inject_scores_requires_auth(self):
        resp = self.client.get("/api/admin/injects/scores")
        assert resp.status_code == 302

    def test_inject_scores_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/injects/scores")
        assert resp.status_code == 403

    def test_inject_scores_success(self):
        template = self._make_template()
        ri = RubricItem(title="Quality", points=100, template=template, order=0)
        db.session.add(ri)
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Graded"
        db.session.add(inject)
        db.session.flush()
        score = InjectRubricScore(score=80, inject=inject, rubric_item=ri, grader=self.white_user)
        db.session.add(score)
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.get("/api/admin/injects/scores")
        assert resp.status_code == 200
        data = resp.json["data"]
        assert len(data) >= 1

    # -----------------------------------------------------------------------
    # GET /api/admin/injects/get_bar_chart
    # -----------------------------------------------------------------------
    def test_inject_bar_chart_requires_auth(self):
        resp = self.client.get("/api/admin/injects/get_bar_chart")
        assert resp.status_code == 302

    def test_inject_bar_chart_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/injects/get_bar_chart")
        assert resp.status_code == 403

    def test_inject_bar_chart_success(self):
        self.login("whiteuser")
        resp = self.client.get("/api/admin/injects/get_bar_chart")
        assert resp.status_code == 200
        assert "labels" in resp.json
        assert "inject_scores" in resp.json

    def test_inject_bar_chart_with_data(self):
        template = self._make_template()
        ri = RubricItem(title="Quality", points=100, template=template, order=0)
        db.session.add(ri)
        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Graded"
        db.session.add(inject)
        db.session.flush()
        score = InjectRubricScore(score=75, inject=inject, rubric_item=ri, grader=self.white_user)
        db.session.add(score)
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.get("/api/admin/injects/get_bar_chart")
        assert resp.status_code == 200
        assert "Blue Team" in resp.json["labels"]

    # -----------------------------------------------------------------------
    # POST /api/admin/admin_update_template
    # -----------------------------------------------------------------------
    def test_admin_update_template_requires_auth(self):
        resp = self.client.post("/api/admin/admin_update_template")
        assert resp.status_code == 302

    def test_admin_update_template_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post("/api/admin/admin_update_template", data={"pk": 1, "name": "template_state", "value": "x"})
        assert resp.json["error"] == "Incorrect permissions"

    def test_admin_update_template_not_found(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/admin_update_template", data={"pk": 99999, "name": "template_state", "value": "x"}
        )
        assert resp.json["error"] == "Template Not Found"

    def test_admin_update_template_state(self):
        template = self._make_template()
        db.session.commit()
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/admin_update_template",
            data={"pk": template.id, "name": "template_state", "value": "Active"},
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Property Information"

    def test_admin_update_template_points(self):
        template = self._make_template()
        db.session.commit()
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/admin_update_template",
            data={"pk": template.id, "name": "template_points", "value": "500"},
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Property Information"

    # -----------------------------------------------------------------------
    # GET /api/admin/get_teams
    # -----------------------------------------------------------------------
    def test_get_teams_requires_auth(self):
        resp = self.client.get("/api/admin/get_teams")
        assert resp.status_code == 302

    def test_get_teams_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/get_teams")
        assert resp.status_code == 403

    def test_get_teams_success(self):
        self.login("whiteuser")
        resp = self.client.get("/api/admin/get_teams")
        assert resp.status_code == 200
        data = resp.json["data"]
        team_names = [t["name"] for t in data]
        assert "White Team" in team_names
        assert "Blue Team" in team_names
        assert "Red Team" in team_names
        # Verify users are included
        blue = next(t for t in data if t["name"] == "Blue Team")
        assert "blueuser" in blue["users"]

    # -----------------------------------------------------------------------
    # POST /api/admin/update_password
    # -----------------------------------------------------------------------
    def test_update_password_requires_auth(self):
        resp = self.client.post("/api/admin/update_password")
        assert resp.status_code == 302

    def test_update_password_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/update_password",
            data={"user_id": self.blue_user.id, "password": "newpass"},
        )
        assert resp.status_code == 403

    def test_update_password_success(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_password",
            data={"user_id": self.blue_user.id, "password": "newpassword"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Verify user can login with new password
        self.logout()
        resp = self.login("blueuser", "newpassword")
        assert resp.status_code == 200

    def test_update_password_missing_fields(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/update_password", data={}, follow_redirects=True)
        assert resp.status_code == 200  # Redirects with flash

    def test_update_password_invalid_user(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_password",
            data={"user_id": 99999, "password": "newpass"},
            follow_redirects=True,
        )
        # Should redirect to login when user not found
        assert resp.status_code == 200

    # -----------------------------------------------------------------------
    # POST /api/admin/add_user
    # -----------------------------------------------------------------------
    def test_add_user_requires_auth(self):
        resp = self.client.post("/api/admin/add_user")
        assert resp.status_code == 302

    def test_add_user_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/add_user",
            data={"username": "newuser", "password": "pass", "team_id": self.blue_team.id},
        )
        assert resp.status_code == 403

    def test_add_user_success(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/add_user",
            data={"username": "newblue", "password": "testpass", "team_id": self.blue_team.id},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        user = db.session.query(User).filter_by(username="newblue").first()
        assert user is not None
        assert user.team.id == self.blue_team.id

    def test_add_user_missing_fields(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/add_user", data={"username": "partial"}, follow_redirects=True)
        assert resp.status_code == 200  # Redirects with flash

    # -----------------------------------------------------------------------
    # POST /api/admin/add_team
    # -----------------------------------------------------------------------
    def test_add_team_requires_auth(self):
        resp = self.client.post("/api/admin/add_team")
        assert resp.status_code == 302

    def test_add_team_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.post("/api/admin/add_team", data={"name": "New", "color": "Blue"})
        assert resp.status_code == 403

    def test_add_team_success(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/add_team",
            data={"name": "New Blue Team", "color": "Blue"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        team = db.session.query(Team).filter_by(name="New Blue Team").first()
        assert team is not None
        assert team.color == "Blue"

    def test_add_team_missing_fields(self):
        self.login("whiteuser")
        resp = self.client.post("/api/admin/add_team", data={"name": "Only Name"}, follow_redirects=True)
        assert resp.status_code == 200  # Redirects with flash

    # -----------------------------------------------------------------------
    # GET /api/admin/get_engine_stats
    # -----------------------------------------------------------------------
    def test_get_engine_stats_requires_auth(self):
        resp = self.client.get("/api/admin/get_engine_stats")
        assert resp.status_code == 302

    def test_get_engine_stats_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/get_engine_stats")
        assert resp.status_code == 403

    def test_get_engine_stats_success(self):
        svc = self._make_service()
        rnd = Round(number=1)
        db.session.add(rnd)
        db.session.flush()
        c1 = Check(service=svc, round=rnd, result=True, output="ok")
        c2 = Check(service=svc, round=rnd, result=False, output="fail")
        db.session.add_all([c1, c2])
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.get("/api/admin/get_engine_stats")
        assert resp.status_code == 200
        data = resp.json
        assert data["round_number"] == 1
        assert data["num_passed_checks"] == 1
        assert data["num_failed_checks"] == 1
        assert data["total_checks"] == 2

    def test_get_engine_stats_no_rounds(self):
        self.login("whiteuser")
        resp = self.client.get("/api/admin/get_engine_stats")
        assert resp.status_code == 200
        assert resp.json["round_number"] == 0
        assert resp.json["total_checks"] == 0

    # -----------------------------------------------------------------------
    # GET /api/admin/get_worker_stats
    # -----------------------------------------------------------------------
    def test_get_worker_stats_requires_auth(self):
        resp = self.client.get("/api/admin/get_worker_stats")
        assert resp.status_code == 302

    def test_get_worker_stats_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/get_worker_stats")
        assert resp.status_code == 403

    def test_get_worker_stats_success(self):
        self.login("whiteuser")
        with patch("scoring_engine.web.views.api.admin.CeleryStats") as mock_cs:
            mock_cs.get_worker_stats.return_value = {"worker1": {"status": "active"}}
            resp = self.client.get("/api/admin/get_worker_stats")
        assert resp.status_code == 200
        assert resp.json["data"] == {"worker1": {"status": "active"}}

    # -----------------------------------------------------------------------
    # GET /api/admin/get_queue_stats
    # -----------------------------------------------------------------------
    def test_get_queue_stats_requires_auth(self):
        resp = self.client.get("/api/admin/get_queue_stats")
        assert resp.status_code == 302

    def test_get_queue_stats_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/get_queue_stats")
        assert resp.status_code == 403

    def test_get_queue_stats_success(self):
        self.login("whiteuser")
        with patch("scoring_engine.web.views.api.admin.CeleryStats") as mock_cs:
            mock_cs.get_queue_stats.return_value = {"default": 5}
            resp = self.client.get("/api/admin/get_queue_stats")
        assert resp.status_code == 200
        assert resp.json["data"] == {"default": 5}

    # -----------------------------------------------------------------------
    # GET /api/admin/get_competition_summary
    # -----------------------------------------------------------------------
    def test_get_competition_summary_requires_auth(self):
        resp = self.client.get("/api/admin/get_competition_summary")
        assert resp.status_code == 302

    def test_get_competition_summary_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/get_competition_summary")
        assert resp.status_code == 403

    def test_get_competition_summary_empty(self):
        self.login("whiteuser")
        resp = self.client.get("/api/admin/get_competition_summary")
        assert resp.status_code == 200
        data = resp.json
        assert data["blue_teams"] == 1  # From three_teams fixture
        assert data["total_services"] == 0
        assert data["overall_uptime"] == 0.0
        assert data["currently_passing"] == 0

    def test_get_competition_summary_with_data(self):
        svc = self._make_service()
        rnd = Round(number=1)
        db.session.add(rnd)
        db.session.flush()
        c1 = Check(service=svc, round=rnd, result=True, output="ok")
        c2 = Check(service=svc, round=rnd, result=False, output="fail")
        db.session.add_all([c1, c2])
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.get("/api/admin/get_competition_summary")
        assert resp.status_code == 200
        data = resp.json
        assert data["blue_teams"] == 1
        assert data["total_services"] == 1
        assert data["overall_uptime"] == 50.0
        assert data["currently_passing"] == 1

    # -----------------------------------------------------------------------
    # GET /api/admin/welcome/config
    # -----------------------------------------------------------------------
    def test_get_welcome_config_requires_auth(self):
        resp = self.client.get("/api/admin/welcome/config")
        assert resp.status_code == 302

    def test_get_welcome_config_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.get("/api/admin/welcome/config")
        assert resp.status_code == 403

    def test_get_welcome_config_success(self):
        self.login("whiteuser")
        resp = self.client.get("/api/admin/welcome/config")
        assert resp.status_code == 200
        data = resp.json["data"]
        assert "welcome_message" in data
        assert "sponsor_tiers" in data

    # -----------------------------------------------------------------------
    # PUT /api/admin/welcome/config
    # -----------------------------------------------------------------------
    def test_put_welcome_config_requires_auth(self):
        resp = self.client.put("/api/admin/welcome/config", json={})
        assert resp.status_code == 302

    def test_put_welcome_config_requires_white_team(self):
        self.login("blueuser")
        resp = self.client.put("/api/admin/welcome/config", json={})
        assert resp.status_code == 403

    def test_put_welcome_config_no_data(self):
        self.login("whiteuser")
        # Send empty dict which is falsy in `if not data` check
        resp = self.client.put(
            "/api/admin/welcome/config",
            json={},
        )
        assert resp.status_code == 400
        assert resp.json["status"] == "Error"

    def test_put_welcome_config_success(self):
        self.login("whiteuser")
        resp = self.client.put(
            "/api/admin/welcome/config",
            json={
                "welcome_message": "<h1>Hello</h1>",
                "sponsor_tiers": [
                    {"name": "Gold", "display_order": 1, "sponsors": [{"name": "Acme Corp"}]},
                ],
            },
        )
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"
        assert resp.json["data"]["welcome_message"] == "<h1>Hello</h1>"

    def test_put_welcome_config_invalid_structure(self):
        self.login("whiteuser")
        resp = self.client.put(
            "/api/admin/welcome/config",
            json={
                "welcome_message": "Hello",
                "sponsor_tiers": [
                    "not a dict",
                ],
            },
        )
        assert resp.status_code == 400
        assert resp.json["status"] == "Error"
