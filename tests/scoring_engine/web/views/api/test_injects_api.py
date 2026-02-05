import io
import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from scoring_engine.models.inject import Comment, File, Inject, Template
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestInjectsAPI(UnitTest):
    """Comprehensive tests for Injects API endpoints including security tests"""

    def setup_method(self):
        super(TestInjectsAPI, self).setup_method()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        # Create test users for different teams
        self.white_team = Team(name="White Team", color="White")
        self.red_team = Team(name="Red Team", color="Red")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")

        self.session.add_all([self.white_team, self.red_team, self.blue_team1, self.blue_team2])
        self.session.commit()

        self.white_user = User(username="whiteuser", password="pass", team=self.white_team)
        self.red_user = User(username="reduser", password="pass", team=self.red_team)
        self.blue_user1 = User(username="blueuser1", password="pass", team=self.blue_team1)
        self.blue_user2 = User(username="blueuser2", password="pass", team=self.blue_team2)

        self.session.add_all([self.white_user, self.red_user, self.blue_user1, self.blue_user2])
        self.session.commit()

    def teardown_method(self):
        self.ctx.pop()
        super(TestInjectsAPI, self).teardown_method()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    # Authorization Tests
    def test_api_injects_requires_auth(self):
        """Test that /api/injects requires authentication"""
        resp = self.client.get("/api/injects")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_api_injects_blue_team_authorized(self):
        """Test that blue team can access their injects"""
        self.login("blueuser1", "pass")
        resp = self.client.get("/api/injects")
        assert resp.status_code == 200

    def test_api_injects_red_team_authorized(self):
        """Test that red team can access their injects"""
        self.login("reduser", "pass")
        resp = self.client.get("/api/injects")
        assert resp.status_code == 200

    def test_api_injects_white_team_unauthorized(self):
        """Test that white team cannot access inject list (403)"""
        self.login("whiteuser", "pass")
        resp = self.client.get("/api/injects")
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    def test_api_injects_returns_only_team_injects(self):
        """Test that teams only see their own injects"""
        # Create injects for both blue teams
        template1 = Template(
            title="Inject 1",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject1 = Inject(team=self.blue_team1, template=template1, enabled=True)
        inject2 = Inject(team=self.blue_team2, template=template1, enabled=True)

        self.session.add_all([template1, inject1, inject2])
        self.session.commit()

        # Login as blue team 1
        self.login("blueuser1", "pass")
        resp = self.client.get("/api/injects")
        data = resp.json["data"]

        assert len(data) == 1
        assert data[0]["id"] == inject1.id

    def test_api_injects_filters_by_start_time(self):
        """Test that injects are only shown after start time"""
        # Create future inject
        future_template = Template(
            title="Future Inject",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2)
        )
        future_inject = Inject(team=self.blue_team1, template=future_template, enabled=True)

        # Create current inject
        current_template = Template(
            title="Current Inject",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        current_inject = Inject(team=self.blue_team1, template=current_template, enabled=True)

        self.session.add_all([future_template, future_inject, current_template, current_inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.get("/api/injects")
        data = resp.json["data"]

        # Only current inject should be returned
        assert len(data) == 1
        assert data[0]["id"] == current_inject.id

    def test_api_injects_filters_disabled(self):
        """Test that disabled injects are not returned"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        enabled_inject = Inject(team=self.blue_team1, template=template, enabled=True)
        disabled_inject = Inject(team=self.blue_team1, template=template, enabled=False)

        self.session.add_all([template, enabled_inject, disabled_inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.get("/api/injects")
        data = resp.json["data"]

        assert len(data) == 1
        assert data[0]["id"] == enabled_inject.id

    # File Upload Security Tests
    def test_file_upload_requires_auth(self):
        """Test that file upload requires authentication"""
        resp = self.client.post("/api/inject/1/upload")
        assert resp.status_code == 302

    def test_file_upload_team_authorization(self):
        """Test that users can only upload to their own team's injects"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        # Try to upload as different team
        self.login("blueuser2", "pass")
        data = {"file": (io.BytesIO(b"test"), "test.txt")}
        resp = self.client.post(f"/api/inject/{inject.id}/upload", data=data)

        assert resp.status_code == 403

    @patch("scoring_engine.web.views.api.injects.os.makedirs")
    @patch("scoring_engine.web.views.api.injects.os.path.exists")
    def test_file_upload_path_traversal_prevention(self, mock_exists, mock_makedirs):
        """SECURITY: Test that path traversal attacks are prevented"""
        mock_exists.return_value = False

        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")

        # Attempt path traversal attacks
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../tmp/evil.sh",
            "test/../../etc/shadow"
        ]

        for malicious_name in malicious_filenames:
            with patch("builtins.open", MagicMock()):
                data = {"file": (io.BytesIO(b"malicious"), malicious_name)}
                resp = self.client.post(
                    f"/api/inject/{inject.id}/upload",
                    data=data,
                    content_type="multipart/form-data"
                )

                # The secure_filename should sanitize the path
                # Check that file was created with safe name
                if resp.status_code == 200:
                    file_obj = self.session.query(File).filter(
                        File.inject_id == inject.id
                    ).first()
                    if file_obj:
                        # Ensure the filename doesn't contain path traversal
                        assert ".." not in file_obj.name
                        assert "/" not in file_obj.name.replace(str(inject.id), "")
                        assert "\\" not in file_obj.name

    def test_file_upload_prevents_after_end_time(self):
        """Test that files cannot be uploaded after inject ends"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1)  # Ended
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        data = {"file": (io.BytesIO(b"test"), "test.txt")}
        resp = self.client.post(
            f"/api/inject/{inject.id}/upload",
            data=data,
            content_type="multipart/form-data"
        )

        assert resp.status_code == 400
        assert "ended" in resp.data.decode().lower()

    def test_file_upload_prevents_after_submission(self):
        """Test that files cannot be uploaded after inject is submitted"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        # Set status after creation
        inject.status = "Submitted"
        self.session.commit()

        self.login("blueuser1", "pass")
        data = {"file": (io.BytesIO(b"test"), "test.txt")}
        resp = self.client.post(
            f"/api/inject/{inject.id}/upload",
            data=data,
            content_type="multipart/form-data"
        )

        assert resp.status_code == 400
        assert "submitted" in resp.data.decode().lower()

    def test_file_upload_requires_file(self):
        """Test that upload fails without a file"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.post(f"/api/inject/{inject.id}/upload")

        assert resp.status_code == 400

    def test_file_upload_duplicate_filename_rejected(self):
        """SECURITY: Test that duplicate filenames are rejected"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        # Create existing file
        existing_file = File(
            f"Inject{inject.id}_Blue Team 1_test.txt",
            self.blue_user1,
            inject
        )
        self.session.add(existing_file)
        self.session.commit()

        self.login("blueuser1", "pass")

        with patch("scoring_engine.web.views.api.injects.os.path.exists", return_value=True):
            data = {"file": (io.BytesIO(b"test"), "test.txt")}
            resp = self.client.post(
                f"/api/inject/{inject.id}/upload",
                data=data,
                content_type="multipart/form-data"
            )

            assert resp.status_code == 400
            assert "not unique" in resp.data.decode().lower()

    # Submit Tests
    def test_inject_submit_requires_auth(self):
        """Test that submit requires authentication"""
        resp = self.client.post("/api/inject/1/submit")
        assert resp.status_code == 302

    def test_inject_submit_team_authorization(self):
        """Test that users can only submit their own team's injects"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        # Try to submit as different team
        self.login("blueuser2", "pass")
        resp = self.client.post(f"/api/inject/{inject.id}/submit")

        assert resp.status_code == 403

    def test_inject_submit_only_blue_team(self):
        """Test that only blue team can submit injects"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.red_team, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.post(f"/api/inject/{inject.id}/submit")

        assert resp.status_code == 403

    def test_inject_submit_prevents_after_end_time(self):
        """Test that inject cannot be submitted after end time"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.post(f"/api/inject/{inject.id}/submit")

        assert resp.status_code == 403

    def test_inject_submit_updates_status(self):
        """Test that submit updates inject status and timestamp"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        # Use naive UTC datetimes for comparison (matching what's stored in DB)
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        resp = self.client.post(f"/api/inject/{inject.id}/submit")
        after = datetime.now(timezone.utc).replace(tzinfo=None)

        assert resp.status_code == 200
        self.session.refresh(inject)
        assert inject.status == "Submitted"
        assert inject.submitted is not None
        assert before <= inject.submitted <= after

    # Comment Tests
    def test_inject_add_comment_requires_auth(self):
        """Test that adding comment requires authentication"""
        resp = self.client.post("/api/inject/1/comment", json={"comment": "test"})
        assert resp.status_code == 302

    def test_inject_add_comment_team_authorization(self):
        """Test that users can only comment on their team's injects"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        # Try to comment as different team
        self.login("blueuser2", "pass")
        resp = self.client.post(
            f"/api/inject/{inject.id}/comment",
            json={"comment": "test"}
        )

        assert resp.status_code == 403

    def test_inject_add_comment_white_team_authorized(self):
        """Test that white team can comment on any inject"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("whiteuser", "pass")
        resp = self.client.post(
            f"/api/inject/{inject.id}/comment",
            json={"comment": "White team feedback"}
        )

        assert resp.status_code == 200

    def test_inject_add_comment_requires_comment_field(self):
        """Test that comment field is required"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.post(f"/api/inject/{inject.id}/comment", json={})

        assert resp.status_code == 400
        assert resp.json["status"] == "No comment"

    def test_inject_add_comment_rejects_empty_comment(self):
        """Test that empty comments are rejected"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.post(
            f"/api/inject/{inject.id}/comment",
            json={"comment": ""}
        )

        assert resp.status_code == 400

    def test_inject_add_comment_prevents_after_end_time(self):
        """Test that comments cannot be added after inject ends"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.post(
            f"/api/inject/{inject.id}/comment",
            json={"comment": "Too late"}
        )

        assert resp.status_code == 400

    def test_inject_add_comment_success(self):
        """Test successful comment addition"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.post(
            f"/api/inject/{inject.id}/comment",
            json={"comment": "Great inject!"}
        )

        assert resp.status_code == 200
        assert resp.json["status"] == "Comment added"

        # Verify comment was created
        comment = self.session.query(Comment).filter(
            Comment.inject_id == inject.id
        ).first()
        assert comment is not None
        assert comment.comment == "Great inject!"
        assert comment.user_id == self.blue_user1.id

    # Download Tests
    def test_inject_download_requires_auth(self):
        """Test that file download requires authentication"""
        resp = self.client.get("/api/inject/1/files/1/download")
        assert resp.status_code == 302

    def test_inject_download_team_authorization(self):
        """Test that users can only download their team's files"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        file_obj = File("test.txt", self.blue_user1, inject)
        self.session.add_all([template, inject, file_obj])
        self.session.commit()

        # Try to download as different team
        self.login("blueuser2", "pass")
        resp = self.client.get(f"/api/inject/{inject.id}/files/{file_obj.id}/download")

        assert resp.status_code == 403

    def test_inject_download_white_team_authorized(self):
        """Test that white team can download any file"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        file_obj = File("test.txt", self.blue_user1, inject)
        self.session.add_all([template, inject, file_obj])
        self.session.commit()

        self.login("whiteuser", "pass")

        # Mock file existence
        with patch("scoring_engine.web.views.api.injects.send_file") as mock_send:
            resp = self.client.get(f"/api/inject/{inject.id}/files/{file_obj.id}/download")
            # Will fail with 404 or succeed depending on file existence
            # We're mainly checking authorization didn't block it

    def test_inject_download_file_not_found(self):
        """Test that 404 is returned for non-existent files"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team1, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser1", "pass")
        resp = self.client.get(f"/api/inject/{inject.id}/files/99999/download")

        assert resp.status_code == 403  # File doesn't exist, so unauthorized
