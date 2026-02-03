"""Tests for Announcements API endpoints"""
import json

from scoring_engine.models.announcement import Announcement, AnnouncementRead
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestAnnouncementsAPI(UnitTest):

    def setup_method(self):
        super(TestAnnouncementsAPI, self).setup_method()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")
        self.session.add_all([
            self.white_team,
            self.blue_team1,
            self.blue_team2,
            self.red_team,
        ])
        self.session.commit()

        # Create users
        self.white_user = User(
            username="whiteuser", password="pass", team=self.white_team
        )
        self.blue_user1 = User(
            username="blueuser1", password="pass", team=self.blue_team1
        )
        self.blue_user2 = User(
            username="blueuser2", password="pass", team=self.blue_team2
        )
        self.red_user = User(
            username="reduser", password="pass", team=self.red_team
        )
        self.session.add_all([
            self.white_user,
            self.blue_user1,
            self.blue_user2,
            self.red_user,
        ])
        self.session.commit()

    def teardown_method(self):
        self.ctx.pop()
        super(TestAnnouncementsAPI, self).teardown_method()

    def login(self, username, password="pass"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    # --- Public API: GET /api/announcements ---

    def test_get_announcements_unauthenticated_sees_global(self):
        """Unauthenticated users see global announcements"""
        self.session.add(Announcement(
            title="Global", content="Hello", audience="global"
        ))
        self.session.add(Announcement(
            title="Blue Only", content="Hi", audience="all_blue"
        ))
        self.session.commit()
        resp = self.client.get("/api/announcements")
        assert resp.status_code == 200
        data = resp.json["data"]
        assert len(data) == 1
        assert data[0]["title"] == "Global"

    def test_get_announcements_blue_sees_blue(self):
        """Blue team sees global + all_blue announcements"""
        self.session.add(Announcement(
            title="Global", content="G", audience="global"
        ))
        self.session.add(Announcement(
            title="Blue", content="B", audience="all_blue"
        ))
        self.session.add(Announcement(
            title="Red", content="R", audience="all_red"
        ))
        self.session.commit()
        self.login("blueuser1")
        resp = self.client.get("/api/announcements")
        data = resp.json["data"]
        titles = [a["title"] for a in data]
        assert "Global" in titles
        assert "Blue" in titles
        assert "Red" not in titles

    def test_get_announcements_red_sees_red(self):
        """Red team sees global + all_red announcements"""
        self.session.add(Announcement(
            title="Global", content="G", audience="global"
        ))
        self.session.add(Announcement(
            title="Blue", content="B", audience="all_blue"
        ))
        self.session.add(Announcement(
            title="Red", content="R", audience="all_red"
        ))
        self.session.commit()
        self.login("reduser")
        resp = self.client.get("/api/announcements")
        data = resp.json["data"]
        titles = [a["title"] for a in data]
        assert "Global" in titles
        assert "Red" in titles
        assert "Blue" not in titles

    def test_get_announcements_team_specific(self):
        """Team-specific announcements only visible to that team"""
        audience = f"team:{self.blue_team1.id}"
        self.session.add(Announcement(
            title="For Team 1", content="T", audience=audience
        ))
        self.session.commit()

        self.login("blueuser1")
        resp = self.client.get("/api/announcements")
        assert len(resp.json["data"]) == 1

        self.logout()
        self.login("blueuser2")
        resp = self.client.get("/api/announcements")
        assert len(resp.json["data"]) == 0

    def test_get_announcements_multi_team(self):
        """Multi-team announcements visible to specified teams"""
        audience = f"teams:{self.blue_team1.id},{self.blue_team2.id}"
        self.session.add(Announcement(
            title="For Both", content="T", audience=audience
        ))
        self.session.commit()

        self.login("blueuser1")
        resp = self.client.get("/api/announcements")
        assert len(resp.json["data"]) == 1

        self.logout()
        self.login("blueuser2")
        resp = self.client.get("/api/announcements")
        assert len(resp.json["data"]) == 1

        self.logout()
        self.login("reduser")
        resp = self.client.get("/api/announcements")
        assert len(resp.json["data"]) == 0

    def test_get_announcements_pinned_first(self):
        """Pinned announcements appear first"""
        ann1 = Announcement(title="Regular", content="R")
        ann2 = Announcement(title="Pinned", content="P")
        ann2.is_pinned = True
        self.session.add_all([ann1, ann2])
        self.session.commit()
        resp = self.client.get("/api/announcements")
        data = resp.json["data"]
        assert data[0]["title"] == "Pinned"

    def test_get_announcements_inactive_hidden(self):
        """Inactive announcements are not shown"""
        ann = Announcement(title="Inactive", content="I")
        ann.is_active = False
        self.session.add(ann)
        self.session.commit()
        resp = self.client.get("/api/announcements")
        assert len(resp.json["data"]) == 0

    def test_get_announcements_marks_as_read(self):
        """Viewing announcements marks them as read for the user"""
        self.session.add(Announcement(
            title="Test", content="T", audience="global"
        ))
        self.session.commit()
        self.login("blueuser1")
        self.client.get("/api/announcements")
        read = (
            self.session.query(AnnouncementRead)
            .filter_by(user_id=self.blue_user1.id)
            .first()
        )
        assert read is not None

    # --- Public API: GET /api/announcements/unread_count ---

    def test_unread_count_all_unread(self):
        """All announcements are unread for a new user"""
        self.session.add(Announcement(
            title="A1", content="C", audience="global"
        ))
        self.session.add(Announcement(
            title="A2", content="C", audience="global"
        ))
        self.session.commit()
        self.login("blueuser1")
        resp = self.client.get("/api/announcements/unread_count")
        assert resp.json["count"] == 2

    def test_unread_count_after_read(self):
        """Count is zero after viewing announcements"""
        self.session.add(Announcement(
            title="A1", content="C", audience="global"
        ))
        self.session.commit()
        self.login("blueuser1")
        # View to mark as read
        self.client.get("/api/announcements")
        resp = self.client.get("/api/announcements/unread_count")
        assert resp.json["count"] == 0

    def test_unread_count_only_counts_visible(self):
        """Unread count only includes announcements visible to user"""
        self.session.add(Announcement(
            title="Global", content="C", audience="global"
        ))
        self.session.add(Announcement(
            title="Red Only", content="C", audience="all_red"
        ))
        self.session.commit()
        self.login("blueuser1")
        resp = self.client.get("/api/announcements/unread_count")
        # Blue user should only see global, not red
        assert resp.json["count"] == 1

    # --- Public API: POST /api/announcements/mark_read ---

    def test_mark_read_requires_auth(self):
        """mark_read endpoint requires authentication"""
        resp = self.client.post("/api/announcements/mark_read")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_mark_read_clears_badge(self):
        """Explicitly marking as read clears unread count"""
        self.session.add(Announcement(
            title="A1", content="C", audience="global"
        ))
        self.session.commit()
        self.login("blueuser1")
        # Verify unread first
        resp = self.client.get("/api/announcements/unread_count")
        assert resp.json["count"] == 1
        # Mark as read
        resp = self.client.post("/api/announcements/mark_read")
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"
        # Verify cleared
        resp = self.client.get("/api/announcements/unread_count")
        assert resp.json["count"] == 0

    # --- Admin API: Create ---

    def test_admin_create_requires_auth(self):
        """Admin create requires authentication"""
        resp = self.client.post(
            "/api/admin/announcements",
            content_type="application/json",
            data=json.dumps({"title": "T", "content": "C"}),
        )
        assert resp.status_code == 302

    def test_admin_create_requires_white_team(self):
        """Admin create requires white team"""
        self.login("blueuser1")
        resp = self.client.post(
            "/api/admin/announcements",
            content_type="application/json",
            data=json.dumps({"title": "T", "content": "C"}),
        )
        assert resp.status_code == 403

    def test_admin_create_success(self):
        """White team can create announcements"""
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/announcements",
            content_type="application/json",
            data=json.dumps({
                "title": "New Announcement",
                "content": "<p>Hello</p>",
                "audience": "all_blue",
                "is_pinned": True,
            }),
        )
        assert resp.status_code == 201
        assert resp.json["data"]["title"] == "New Announcement"
        assert resp.json["data"]["audience"] == "all_blue"
        assert resp.json["data"]["is_pinned"] is True

    def test_admin_create_missing_title(self):
        """Create fails without title"""
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/announcements",
            content_type="application/json",
            data=json.dumps({"content": "C"}),
        )
        assert resp.status_code == 400

    def test_admin_create_missing_content(self):
        """Create fails without content"""
        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/announcements",
            content_type="application/json",
            data=json.dumps({"title": "T"}),
        )
        assert resp.status_code == 400

    # --- Admin API: Update ---

    def test_admin_update_success(self):
        """White team can update announcements"""
        ann = Announcement(title="Old", content="Old content")
        self.session.add(ann)
        self.session.commit()
        self.login("whiteuser")
        resp = self.client.put(
            f"/api/admin/announcements/{ann.id}",
            content_type="application/json",
            data=json.dumps({
                "title": "Updated",
                "content": "New content",
                "audience": "all_red",
            }),
        )
        assert resp.status_code == 200
        assert resp.json["data"]["title"] == "Updated"
        assert resp.json["data"]["audience"] == "all_red"

    def test_admin_update_requires_white_team(self):
        """Blue team cannot update announcements"""
        ann = Announcement(title="T", content="C")
        self.session.add(ann)
        self.session.commit()
        self.login("blueuser1")
        resp = self.client.put(
            f"/api/admin/announcements/{ann.id}",
            content_type="application/json",
            data=json.dumps({"title": "Hacked"}),
        )
        assert resp.status_code == 403

    def test_admin_update_not_found(self):
        """Update returns 404 for nonexistent announcement"""
        self.login("whiteuser")
        resp = self.client.put(
            "/api/admin/announcements/99999",
            content_type="application/json",
            data=json.dumps({"title": "X"}),
        )
        assert resp.status_code == 404

    # --- Admin API: Delete ---

    def test_admin_delete_success(self):
        """White team can delete announcements"""
        ann = Announcement(title="Delete Me", content="C")
        self.session.add(ann)
        self.session.commit()
        ann_id = ann.id
        self.login("whiteuser")
        resp = self.client.delete(
            f"/api/admin/announcements/{ann_id}"
        )
        assert resp.status_code == 200
        assert self.session.get(Announcement, ann_id) is None

    def test_admin_delete_requires_white_team(self):
        """Blue team cannot delete announcements"""
        ann = Announcement(title="T", content="C")
        self.session.add(ann)
        self.session.commit()
        self.login("blueuser1")
        resp = self.client.delete(
            f"/api/admin/announcements/{ann.id}"
        )
        assert resp.status_code == 403

    def test_admin_delete_not_found(self):
        """Delete returns 404 for nonexistent announcement"""
        self.login("whiteuser")
        resp = self.client.delete(
            "/api/admin/announcements/99999"
        )
        assert resp.status_code == 404

    # --- Admin API: Toggle pin/active ---

    def test_admin_toggle_pin(self):
        """White team can toggle pin status"""
        ann = Announcement(title="T", content="C")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_pinned is False
        self.login("whiteuser")
        resp = self.client.post(
            f"/api/admin/announcements/{ann.id}/toggle_pin"
        )
        assert resp.status_code == 200
        assert resp.json["is_pinned"] is True
        # Toggle again
        resp = self.client.post(
            f"/api/admin/announcements/{ann.id}/toggle_pin"
        )
        assert resp.json["is_pinned"] is False

    def test_admin_toggle_active(self):
        """White team can toggle active status"""
        ann = Announcement(title="T", content="C")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_active is True
        self.login("whiteuser")
        resp = self.client.post(
            f"/api/admin/announcements/{ann.id}/toggle_active"
        )
        assert resp.status_code == 200
        assert resp.json["is_active"] is False

    def test_admin_toggle_pin_requires_white_team(self):
        """Blue team cannot toggle pin"""
        ann = Announcement(title="T", content="C")
        self.session.add(ann)
        self.session.commit()
        self.login("blueuser1")
        resp = self.client.post(
            f"/api/admin/announcements/{ann.id}/toggle_pin"
        )
        assert resp.status_code == 403

    # --- Admin API: Get all/single ---

    def test_admin_get_all_includes_inactive(self):
        """Admin list includes inactive announcements"""
        ann1 = Announcement(title="Active", content="C")
        ann2 = Announcement(title="Inactive", content="C")
        ann2.is_active = False
        self.session.add_all([ann1, ann2])
        self.session.commit()
        self.login("whiteuser")
        resp = self.client.get("/api/admin/announcements")
        assert resp.status_code == 200
        assert len(resp.json["data"]) == 2

    def test_admin_get_single(self):
        """Admin can get a single announcement"""
        ann = Announcement(title="Single", content="C")
        self.session.add(ann)
        self.session.commit()
        self.login("whiteuser")
        resp = self.client.get(
            f"/api/admin/announcements/{ann.id}"
        )
        assert resp.status_code == 200
        assert resp.json["data"]["title"] == "Single"

    def test_admin_get_single_not_found(self):
        """Admin get returns 404 for nonexistent"""
        self.login("whiteuser")
        resp = self.client.get(
            "/api/admin/announcements/99999"
        )
        assert resp.status_code == 404

    # --- Teams list API ---

    def test_teams_list_requires_white_team(self):
        """Teams list requires white team"""
        self.login("blueuser1")
        resp = self.client.get("/api/admin/teams/list")
        assert resp.status_code == 403

    def test_teams_list_success(self):
        """White team can list teams"""
        self.login("whiteuser")
        resp = self.client.get("/api/admin/teams/list")
        assert resp.status_code == 200
        assert len(resp.json["data"]) == 4
