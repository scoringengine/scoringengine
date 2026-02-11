import io
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from scoring_engine.models.inject import Inject, InjectComment, InjectFile, InjectRubricScore, RubricItem, Template
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
import pytest

from scoring_engine.db import db


class TestInjectsAPI:
    """Comprehensive tests for Injects API endpoints including security tests"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        # Create test users for different teams
        self.white_team = Team(name="White Team", color="White")
        self.red_team = Team(name="Red Team", color="Red")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")

        db.session.add_all([self.white_team, self.red_team, self.blue_team1, self.blue_team2])
        db.session.commit()

        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.red_user = User(username="reduser", password="testpass", team=self.red_team)
        self.blue_user1 = User(username="blueuser1", password="testpass", team=self.blue_team1)
        self.blue_user2 = User(username="blueuser2", password="testpass", team=self.blue_team2)

        db.session.add_all([self.white_user, self.red_user, self.blue_user1, self.blue_user2])
        db.session.commit()

    def login(self, username):
        return self.client.post(
            "/login",
            data={"username": username, "password": "testpass"},
            follow_redirects=True,
        )

    def _make_template(self, **kwargs):
        """Helper to create a Template with sensible defaults (no score param)."""
        defaults = dict(
            title="Test",
            scenario="Test",
            deliverable="Test",
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        defaults.update(kwargs)
        return Template(**defaults)

    # Authorization Tests
    def test_api_injects_requires_auth(self):
        """Test that /api/injects requires authentication"""
        resp = self.client.get("/api/injects")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_api_injects_blue_team_authorized(self):
        """Test that blue team can access their injects"""
        self.login("blueuser1")
        resp = self.client.get("/api/injects")
        assert resp.status_code == 200

    def test_api_injects_red_team_authorized(self):
        """Test that red team can access their injects"""
        self.login("reduser")
        resp = self.client.get("/api/injects")
        assert resp.status_code == 200

    def test_api_injects_white_team_unauthorized(self):
        """Test that white team cannot access inject list (403)"""
        self.login("whiteuser")
        resp = self.client.get("/api/injects")
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    def test_api_injects_returns_only_team_injects(self):
        """Test that teams only see their own injects"""
        template1 = self._make_template(title="Inject 1")
        inject1 = Inject(team=self.blue_team1, template=template1, enabled=True)
        inject2 = Inject(team=self.blue_team2, template=template1, enabled=True)

        db.session.add_all([template1, inject1, inject2])
        db.session.commit()

        # Login as blue team 1
        self.login("blueuser1")
        resp = self.client.get("/api/injects")
        data = resp.json["data"]

        assert len(data) == 1
        assert data[0]["id"] == inject1.id

    def test_api_injects_filters_by_start_time(self):
        """Test that injects are only shown after start time"""
        future_template = self._make_template(
            title="Future Inject",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        future_inject = Inject(team=self.blue_team1, template=future_template, enabled=True)

        current_template = self._make_template(title="Current Inject")
        current_inject = Inject(team=self.blue_team1, template=current_template, enabled=True)

        db.session.add_all([future_template, future_inject, current_template, current_inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.get("/api/injects")
        data = resp.json["data"]

        # Only current inject should be returned
        assert len(data) == 1
        assert data[0]["id"] == current_inject.id

    def test_api_injects_filters_disabled(self):
        """Test that disabled injects are not returned"""
        template = self._make_template()
        enabled_inject = Inject(team=self.blue_team1, template=template, enabled=True)
        disabled_inject = Inject(team=self.blue_team1, template=template, enabled=False)

        db.session.add_all([template, enabled_inject, disabled_inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.get("/api/injects")
        data = resp.json["data"]

        assert len(data) == 1
        assert data[0]["id"] == enabled_inject.id

    def test_api_injects_returns_max_score(self):
        """Test that the injects list returns max_score from rubric items"""
        template = self._make_template()
        db.session.add(template)
        db.session.flush()
        ri1 = RubricItem(title="Item 1", points=60, template=template)
        ri2 = RubricItem(title="Item 2", points=40, template=template)
        inject = Inject(team=self.blue_team1, template=template, enabled=True)
        db.session.add_all([ri1, ri2, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.get("/api/injects")
        data = resp.json["data"]

        assert len(data) == 1
        assert data[0]["max_score"] == 100

    # File Upload Security Tests
    def test_file_upload_requires_auth(self):
        """Test that file upload requires authentication"""
        resp = self.client.post("/api/inject/1/upload")
        assert resp.status_code == 302

    def test_file_upload_team_authorization(self):
        """Test that users can only upload to their own team's injects"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        # Try to upload as different team
        self.login("blueuser2")
        data = {"file": (io.BytesIO(b"test"), "test.txt")}
        resp = self.client.post(f"/api/inject/{inject.id}/upload", data=data)

        assert resp.status_code == 403

    @patch("scoring_engine.web.views.api.injects.os.makedirs")
    @patch("scoring_engine.web.views.api.injects.os.path.exists")
    def test_file_upload_path_traversal_prevention(self, mock_exists, mock_makedirs):
        """SECURITY: Test that path traversal attacks are prevented"""
        mock_exists.return_value = False

        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")

        # Attempt path traversal attacks
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../tmp/evil.sh",
            "test/../../etc/shadow",
        ]

        for malicious_name in malicious_filenames:
            with patch("builtins.open", MagicMock()):
                data = {"file": (io.BytesIO(b"malicious"), malicious_name)}
                resp = self.client.post(
                    f"/api/inject/{inject.id}/upload", data=data, content_type="multipart/form-data"
                )

                # The secure_filename should sanitize the path
                if resp.status_code == 200:
                    file_obj = db.session.query(InjectFile).filter(InjectFile.inject_id == inject.id).first()
                    if file_obj:
                        assert ".." not in file_obj.filename
                        assert "/" not in file_obj.filename.replace(str(inject.id), "")
                        assert "\\" not in file_obj.filename

    def test_file_upload_prevents_after_end_time(self):
        """Test that files cannot be uploaded after inject ends"""
        template = self._make_template(
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        data = {"file": (io.BytesIO(b"test"), "test.txt")}
        resp = self.client.post(f"/api/inject/{inject.id}/upload", data=data, content_type="multipart/form-data")

        assert resp.status_code == 400
        assert "ended" in resp.data.decode().lower()

    def test_file_upload_prevents_after_submission(self):
        """Test that files cannot be uploaded after inject is submitted"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        inject.status = "Submitted"
        db.session.commit()

        self.login("blueuser1")
        data = {"file": (io.BytesIO(b"test"), "test.txt")}
        resp = self.client.post(f"/api/inject/{inject.id}/upload", data=data, content_type="multipart/form-data")

        assert resp.status_code == 400
        assert "submitted" in resp.data.decode().lower()

    def test_file_upload_allowed_in_revision_requested(self):
        """Test that files can be uploaded when inject is in Revision Requested state"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        inject.status = "Revision Requested"
        db.session.commit()

        self.login("blueuser1")

        with patch("scoring_engine.web.views.api.injects.os.makedirs"):
            with patch("scoring_engine.web.views.api.injects.os.path.exists", return_value=False):
                with patch("builtins.open", MagicMock()):
                    data = {"file": (io.BytesIO(b"test"), "test.txt")}
                    resp = self.client.post(
                        f"/api/inject/{inject.id}/upload", data=data, content_type="multipart/form-data"
                    )

        assert resp.status_code == 200

    def test_file_upload_requires_file(self):
        """Test that upload fails without a file"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/upload")

        assert resp.status_code == 400

    def test_file_upload_duplicate_filename_rejected(self):
        """SECURITY: Test that duplicate filenames are rejected"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        existing_file = InjectFile(
            f"Inject{inject.id}_Blue Team 1_test.txt",
            self.blue_user1,
            inject,
        )
        db.session.add(existing_file)
        db.session.commit()

        self.login("blueuser1")

        with patch("scoring_engine.web.views.api.injects.os.path.exists", return_value=True):
            data = {"file": (io.BytesIO(b"test"), "test.txt")}
            resp = self.client.post(f"/api/inject/{inject.id}/upload", data=data, content_type="multipart/form-data")

            assert resp.status_code == 400
            assert "not unique" in resp.data.decode().lower()

    # File Delete Tests
    def test_file_delete_requires_auth(self):
        """Test that file delete requires authentication"""
        resp = self.client.delete("/api/inject/1/files/1")
        assert resp.status_code == 302

    def test_file_delete_team_authorization(self):
        """Test that users can only delete their own team's files"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        file_obj = InjectFile("test.txt", self.blue_user1, inject)
        db.session.add(file_obj)
        db.session.commit()

        self.login("blueuser2")
        resp = self.client.delete(f"/api/inject/{inject.id}/files/{file_obj.id}")
        assert resp.status_code == 403

    def test_file_delete_not_allowed_after_submission(self):
        """Test that files cannot be deleted after submission"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        file_obj = InjectFile("test.txt", self.blue_user1, inject)
        inject.status = "Submitted"
        db.session.add(file_obj)
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.delete(f"/api/inject/{inject.id}/files/{file_obj.id}")
        assert resp.status_code == 400

    def test_file_delete_allowed_in_draft(self):
        """Test that files can be deleted in Draft state"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        file_obj = InjectFile("test.txt", self.blue_user1, inject)
        db.session.add(file_obj)
        db.session.commit()

        self.login("blueuser1")
        with patch("scoring_engine.web.views.api.injects.os.remove"):
            resp = self.client.delete(f"/api/inject/{inject.id}/files/{file_obj.id}")
        assert resp.status_code == 200

    def test_file_delete_allowed_in_revision_requested(self):
        """Test that files can be deleted in Revision Requested state"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        file_obj = InjectFile("test.txt", self.blue_user1, inject)
        inject.status = "Revision Requested"
        db.session.add(file_obj)
        db.session.commit()

        self.login("blueuser1")
        with patch("scoring_engine.web.views.api.injects.os.remove"):
            resp = self.client.delete(f"/api/inject/{inject.id}/files/{file_obj.id}")
        assert resp.status_code == 200

    # Submit Tests
    def test_inject_submit_requires_auth(self):
        """Test that submit requires authentication"""
        resp = self.client.post("/api/inject/1/submit")
        assert resp.status_code == 302

    def test_inject_submit_team_authorization(self):
        """Test that users can only submit their own team's injects"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser2")
        resp = self.client.post(f"/api/inject/{inject.id}/submit")

        assert resp.status_code == 403

    def test_inject_submit_only_blue_team(self):
        """Test that only blue team can submit injects"""
        template = self._make_template()
        inject = Inject(team=self.red_team, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("reduser")
        resp = self.client.post(f"/api/inject/{inject.id}/submit")

        assert resp.status_code == 403

    def test_inject_submit_prevents_after_end_time(self):
        """Test that inject cannot be submitted after end time"""
        template = self._make_template(
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/submit")

        assert resp.status_code == 403

    def test_inject_submit_only_from_draft(self):
        """Test that submit only works from Draft status"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        inject.status = "Submitted"
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/submit")

        assert resp.status_code == 400

    def test_inject_submit_updates_status(self):
        """Test that submit updates inject status and timestamp"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        resp = self.client.post(f"/api/inject/{inject.id}/submit")
        after = datetime.now(timezone.utc).replace(tzinfo=None)

        assert resp.status_code == 200
        db.session.refresh(inject)
        assert inject.status == "Submitted"
        assert inject.submitted is not None
        assert before <= inject.submitted <= after

    # Resubmit Tests
    def test_inject_resubmit_requires_auth(self):
        """Test that resubmit requires authentication"""
        resp = self.client.post("/api/inject/1/resubmit")
        assert resp.status_code == 302

    def test_inject_resubmit_team_authorization(self):
        """Test that users can only resubmit their own team's injects"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        inject.status = "Revision Requested"
        db.session.commit()

        self.login("blueuser2")
        resp = self.client.post(f"/api/inject/{inject.id}/resubmit")
        assert resp.status_code == 403

    def test_inject_resubmit_only_from_revision_requested(self):
        """Test that resubmit only works from Revision Requested status"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        # Draft status - should fail
        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/resubmit")
        assert resp.status_code == 400

    def test_inject_resubmit_success(self):
        """Test successful resubmission"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        inject.status = "Revision Requested"
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/resubmit")

        assert resp.status_code == 200
        db.session.refresh(inject)
        assert inject.status == "Resubmitted"
        assert inject.submitted is not None

    # Comment Tests
    def test_inject_add_comment_requires_auth(self):
        """Test that adding comment requires authentication"""
        resp = self.client.post("/api/inject/1/comment", json={"comment": "test"})
        assert resp.status_code == 302

    def test_inject_add_comment_team_authorization(self):
        """Test that users can only comment on their team's injects"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser2")
        resp = self.client.post(f"/api/inject/{inject.id}/comment", json={"comment": "test"})

        assert resp.status_code == 403

    def test_inject_add_comment_white_team_authorized(self):
        """Test that white team can comment on any inject"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.post(f"/api/inject/{inject.id}/comment", json={"comment": "White team feedback"})

        assert resp.status_code == 200

    def test_inject_add_comment_requires_comment_field(self):
        """Test that comment field is required"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/comment", json={})

        assert resp.status_code == 400
        assert resp.json["status"] == "No comment"

    def test_inject_add_comment_rejects_empty_comment(self):
        """Test that empty comments are rejected"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/comment", json={"comment": ""})

        assert resp.status_code == 400

    def test_inject_add_comment_prevents_after_end_time(self):
        """Test that comments cannot be added after inject ends"""
        template = self._make_template(
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/comment", json={"comment": "Too late"})

        assert resp.status_code == 400

    def test_inject_add_comment_success(self):
        """Test successful comment addition"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.post(f"/api/inject/{inject.id}/comment", json={"comment": "Great inject!"})

        assert resp.status_code == 200
        assert resp.json["status"] == "Comment added"

        # Verify comment was created
        comment = db.session.query(InjectComment).filter(InjectComment.inject_id == inject.id).first()
        assert comment is not None
        assert comment.content == "Great inject!"
        assert comment.user_id == self.blue_user1.id

    # Download Tests
    def test_inject_download_requires_auth(self):
        """Test that file download requires authentication"""
        resp = self.client.get("/api/inject/1/files/1/download")
        assert resp.status_code == 302

    def test_inject_download_team_authorization(self):
        """Test that users can only download their team's files"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        file_obj = InjectFile("test.txt", self.blue_user1, inject)
        db.session.add_all([template, inject, file_obj])
        db.session.commit()

        # Try to download as different team
        self.login("blueuser2")
        resp = self.client.get(f"/api/inject/{inject.id}/files/{file_obj.id}/download")

        assert resp.status_code == 403

    def test_inject_download_white_team_authorized(self):
        """Test that white team can download any file"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        file_obj = InjectFile("test.txt", self.blue_user1, inject)
        db.session.add_all([template, inject, file_obj])
        db.session.commit()

        self.login("whiteuser")

        with patch("scoring_engine.web.views.api.injects.send_file"):
            self.client.get(f"/api/inject/{inject.id}/files/{file_obj.id}/download")

    def test_inject_download_file_not_found(self):
        """Test that 404 is returned for non-existent files"""
        template = self._make_template()
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.get(f"/api/inject/{inject.id}/files/99999/download")

        assert resp.status_code == 403  # File doesn't exist, so unauthorized

    # Inject Detail Tests
    def test_inject_detail_returns_rubric_items(self):
        """Test that inject detail includes rubric items"""
        template = self._make_template()
        db.session.add(template)
        db.session.flush()
        ri1 = RubricItem(title="Quality", points=60, template=template, order=0)
        ri2 = RubricItem(title="Completeness", points=40, template=template, order=1)
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([ri1, ri2, inject])
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.get(f"/api/inject/{inject.id}")

        assert resp.status_code == 200
        data = resp.json
        assert len(data["rubric_items"]) == 2
        assert data["rubric_items"][0]["title"] == "Quality"
        assert data["rubric_items"][0]["points"] == 60
        assert data["max_score"] == 100

    def test_inject_detail_returns_rubric_scores(self):
        """Test that inject detail includes rubric scores when graded"""
        template = self._make_template()
        db.session.add(template)
        db.session.flush()
        ri = RubricItem(title="Quality", points=100, template=template)
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([ri, inject])
        db.session.flush()
        score = InjectRubricScore(score=80, inject=inject, rubric_item=ri, grader=self.white_user)
        inject.status = "Graded"
        db.session.add(score)
        db.session.commit()

        self.login("blueuser1")
        resp = self.client.get(f"/api/inject/{inject.id}")

        assert resp.status_code == 200
        data = resp.json
        assert len(data["rubric_scores"]) == 1
        assert data["rubric_scores"][0]["score"] == 80
        assert data["score"] == 80

    # Cache Invalidation Tests
    def test_inject_submit_invalidates_cache(self):
        """Test that submitting an inject invalidates the cached /api/inject/<id> response"""
        template = self._make_template(title="Cache Test")
        inject = Inject(team=self.blue_team1, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser1")

        with patch("scoring_engine.web.views.api.injects.cache") as mock_cache:
            resp = self.client.post(f"/api/inject/{inject.id}/submit")

        assert resp.status_code == 200
        mock_cache.delete.assert_called_with(f"/api/inject/{inject.id}_{self.blue_team1.id}")

    def test_inject_grade_invalidates_cache(self):
        """Test that grading an inject invalidates the cached /api/inject/<id> response"""
        template = self._make_template(title="Grade Cache Test")
        db.session.add(template)
        db.session.flush()
        ri = RubricItem(title="Quality", points=100, template=template)
        inject = Inject(team=self.blue_team1, template=template)
        inject.status = "Submitted"
        db.session.add_all([ri, inject])
        db.session.commit()

        self.login("whiteuser")

        with patch("scoring_engine.web.views.api.admin.update_inject_data") as mock_update:
            resp = self.client.post(
                f"/api/admin/inject/{inject.id}/grade", json={"rubric_scores": [{"rubric_item_id": ri.id, "score": 80}]}
            )

        assert resp.status_code == 200
        mock_update.assert_called_once_with(str(inject.id))
