"""Tests for Announcements API endpoints"""
import json

import pytest

from scoring_engine.db import db
from scoring_engine.models.announcement import Announcement
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestAnnouncementsAPI:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")
        db.session.add_all([
            self.white_team,
            self.blue_team1,
            self.blue_team2,
            self.red_team,
        ])
        db.session.commit()

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
        db.session.add_all([
            self.white_user,
            self.blue_user1,
            self.blue_user2,
            self.red_user,
        ])
        db.session.commit()

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
        db.session.add(Announcement(
            title="Global", content="Hello", audience="global"
        ))
        db.session.add(Announcement(
            title="Blue Only", content="Hi", audience="all_blue"
        ))
        db.session.commit()
        resp = self.client.get("/api/announcements")
        assert resp.status_code == 200
        data = resp.json["data"]
        assert len(data) == 1
        assert data[0]["title"] == "Global"

    def test_get_announcements_blue_sees_blue(self):
        """Blue team sees global + all_blue announcements"""
        db.session.add(Announcement(
            title="Global", content="G", audience="global"
        ))
        db.session.add(Announcement(
            title="Blue", content="B", audience="all_blue"
        ))
        db.session.add(Announcement(
            title="Red", content="R", audience="all_red"
        ))
        db.session.commit()
        self.login("blueuser1")
        resp = self.client.get("/api/announcements")
        data = resp.json["data"]
        titles = [a["title"] for a in data]
        assert "Global" in titles
        assert "Blue" in titles
        assert "Red" not in titles

    def test_get_announcements_red_sees_red(self):
        """Red team sees global + all_red announcements"""
        db.session.add(Announcement(
            title="Global", content="G", audience="global"
        ))
        db.session.add(Announcement(
            title="Blue", content="B", audience="all_blue"
        ))
        db.session.add(Announcement(
            title="Red", content="R", audience="all_red"
        ))
        db.session.commit()
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
        db.session.add(Announcement(
            title="For Team 1", content="T", audience=audience
        ))
        db.session.commit()

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
        db.session.add(Announcement(
            title="For Both", content="T", audience=audience
        ))
        db.session.commit()

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
        db.session.add_all([ann1, ann2])
        db.session.commit()
        resp = self.client.get("/api/announcements")
        data = resp.json["data"]
        assert data[0]["title"] == "Pinned"

    def test_get_announcements_inactive_hidden(self):
        """Inactive announcements are not shown"""
        ann = Announcement(title="Inactive", content="I")
        ann.is_active = False
        db.session.add(ann)
        db.session.commit()
        resp = self.client.get("/api/announcements")
        assert len(resp.json["data"]) == 0

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
        db.session.add(ann)
        db.session.commit()
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
        db.session.add(ann)
        db.session.commit()
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
        db.session.add(ann)
        db.session.commit()
        ann_id = ann.id
        self.login("whiteuser")
        resp = self.client.delete(
            f"/api/admin/announcements/{ann_id}"
        )
        assert resp.status_code == 200
        assert db.session.get(Announcement, ann_id) is None

    def test_admin_delete_requires_white_team(self):
        """Blue team cannot delete announcements"""
        ann = Announcement(title="T", content="C")
        db.session.add(ann)
        db.session.commit()
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
        db.session.add(ann)
        db.session.commit()
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
        db.session.add(ann)
        db.session.commit()
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
        db.session.add(ann)
        db.session.commit()
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
        db.session.add_all([ann1, ann2])
        db.session.commit()
        self.login("whiteuser")
        resp = self.client.get("/api/admin/announcements")
        assert resp.status_code == 200
        assert len(resp.json["data"]) == 2

    def test_admin_get_single(self):
        """Admin can get a single announcement"""
        ann = Announcement(title="Single", content="C")
        db.session.add(ann)
        db.session.commit()
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
