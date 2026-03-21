import datetime

from scoring_engine.db import db
from scoring_engine.models.announcement import Announcement
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestAnnouncement:

    def test_init_minimal(self):
        """Test creating an announcement with minimal fields"""
        ann = Announcement(title="Test", content="Hello")
        assert ann.title == "Test"
        assert ann.content == "Hello"
        assert ann.audience == "global"
        assert ann.author_id is None

    def test_init_with_audience(self):
        """Test creating an announcement with custom audience"""
        ann = Announcement(
            title="Blue Only",
            content="Hi blue",
            audience="all_blue",
        )
        assert ann.audience == "all_blue"

    def test_save(self):
        """Test saving an announcement to the database"""
        ann = Announcement(title="Saved", content="Test content")
        db.session.add(ann)
        db.session.commit()
        assert ann.id is not None
        assert ann.created_at is not None

    def test_defaults(self):
        """Test that defaults are applied after commit"""
        ann = Announcement(title="Defaults", content="Check defaults")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_pinned is False
        assert ann.is_active is True
        assert ann.expires_at is None

    def test_to_dict(self):
        """Test serialization to dictionary"""
        ann = Announcement(title="Dict", content="<p>Body</p>")
        db.session.add(ann)
        db.session.commit()
        d = ann.to_dict()
        assert d["id"] == ann.id
        assert d["title"] == "Dict"
        assert d["content"] == "<p>Body</p>"
        assert d["audience"] == "global"
        assert d["is_pinned"] is False
        assert d["is_active"] is True
        assert d["created_at"] is not None
        assert d["expires_at"] is None
        assert d["author_name"] is None

    def test_to_dict_with_author(self):
        """Test serialization includes author username"""
        team = Team(name="White Team", color="White")
        db.session.add(team)
        user = User(username="admin", password="pass", team=team)
        db.session.add(user)
        db.session.commit()
        ann = Announcement(
            title="Authored",
            content="Test",
            author_id=user.id,
        )
        db.session.add(ann)
        db.session.commit()
        d = ann.to_dict()
        assert d["author_name"] == "admin"
        assert d["author_id"] == user.id

    # --- Visibility: Global ---

    def test_global_visible_to_unauthenticated(self):
        """Global announcements are visible to everyone"""
        ann = Announcement(title="G", content="Global", audience="global")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(None) is True

    def test_global_visible_to_blue(self):
        team = Team(name="Blue 1", color="Blue")
        db.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        ann = Announcement(title="G", content="Global")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user) is True

    # --- Visibility: all_blue ---

    def test_all_blue_visible_to_blue_team(self):
        team = Team(name="Blue 1", color="Blue")
        db.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        ann = Announcement(title="B", content="Blue", audience="all_blue")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user) is True

    def test_all_blue_hidden_from_red_team(self):
        team = Team(name="Red Team", color="Red")
        db.session.add(team)
        user = User(username="r1", password="p", team=team)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        ann = Announcement(title="B", content="Blue", audience="all_blue")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user) is False

    def test_all_blue_hidden_from_unauthenticated(self):
        ann = Announcement(title="B", content="Blue", audience="all_blue")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(None) is False

    # --- Visibility: all_red ---

    def test_all_red_visible_to_red_team(self):
        team = Team(name="Red Team", color="Red")
        db.session.add(team)
        user = User(username="r1", password="p", team=team)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        ann = Announcement(title="R", content="Red", audience="all_red")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user) is True

    def test_all_red_hidden_from_blue_team(self):
        team = Team(name="Blue 1", color="Blue")
        db.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        ann = Announcement(title="R", content="Red", audience="all_red")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user) is False

    def test_all_red_hidden_from_unauthenticated(self):
        ann = Announcement(title="R", content="Red", audience="all_red")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(None) is False

    # --- Visibility: team:ID ---

    def test_team_specific_visible_to_correct_team(self):
        team = Team(name="Blue 1", color="Blue")
        db.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        ann = Announcement(
            title="T",
            content="Team",
            audience=f"team:{team.id}",
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user) is True

    def test_team_specific_hidden_from_other_team(self):
        team1 = Team(name="Blue 1", color="Blue")
        team2 = Team(name="Blue 2", color="Blue")
        db.session.add_all([team1, team2])
        db.session.commit()
        user2 = User(username="b2", password="p", team=team2)
        user2.authenticated = True
        db.session.add(user2)
        db.session.commit()
        ann = Announcement(
            title="T",
            content="Team",
            audience=f"team:{team1.id}",
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user2) is False

    def test_team_specific_hidden_from_unauthenticated(self):
        ann = Announcement(title="T", content="Team", audience="team:1")
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(None) is False

    # --- Visibility: teams:1,3,5 ---

    def test_multi_team_visible_to_included_team(self):
        team1 = Team(name="Blue 1", color="Blue")
        team2 = Team(name="Blue 2", color="Blue")
        team3 = Team(name="Blue 3", color="Blue")
        db.session.add_all([team1, team2, team3])
        db.session.commit()
        user1 = User(username="b1", password="p", team=team1)
        user1.authenticated = True
        user3 = User(username="b3", password="p", team=team3)
        user3.authenticated = True
        db.session.add_all([user1, user3])
        db.session.commit()
        audience = f"teams:{team1.id},{team3.id}"
        ann = Announcement(
            title="M",
            content="Multi",
            audience=audience,
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user1) is True
        assert ann.is_visible_to_user(user3) is True

    def test_multi_team_hidden_from_excluded_team(self):
        team1 = Team(name="Blue 1", color="Blue")
        team2 = Team(name="Blue 2", color="Blue")
        db.session.add_all([team1, team2])
        db.session.commit()
        user2 = User(username="b2", password="p", team=team2)
        user2.authenticated = True
        db.session.add(user2)
        db.session.commit()
        ann = Announcement(
            title="M",
            content="Multi",
            audience=f"teams:{team1.id}",
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user2) is False

    # --- Visibility: white team sees all ---

    def test_white_team_sees_team_specific(self):
        white = Team(name="White Team", color="White")
        blue = Team(name="Blue 1", color="Blue")
        db.session.add_all([white, blue])
        db.session.commit()
        admin = User(username="admin", password="p", team=white)
        admin.authenticated = True
        db.session.add(admin)
        db.session.commit()
        ann = Announcement(
            title="T",
            content="Team",
            audience=f"team:{blue.id}",
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(admin) is True

    def test_white_team_sees_all_blue(self):
        white = Team(name="White Team", color="White")
        db.session.add(white)
        admin = User(username="admin", password="p", team=white)
        admin.authenticated = True
        db.session.add(admin)
        db.session.commit()
        ann = Announcement(
            title="B",
            content="Blue",
            audience="all_blue",
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(admin) is True

    # --- Visibility: inactive / expired ---

    def test_inactive_hidden(self):
        ann = Announcement(title="I", content="Inactive")
        ann.is_active = False
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(None) is False

    def test_expired_hidden(self):
        ann = Announcement(title="E", content="Expired")
        ann.expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(
            hours=1
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(None) is False

    def test_future_expiry_visible(self):
        ann = Announcement(title="F", content="Future")
        ann.expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(
            hours=1
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(None) is True

    # --- Bad audience values ---

    def test_bad_team_id_hidden(self):
        team = Team(name="Blue 1", color="Blue")
        db.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        ann = Announcement(
            title="Bad", content="Bad", audience="team:notanumber"
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user) is False

    def test_bad_teams_value_hidden(self):
        team = Team(name="Blue 1", color="Blue")
        db.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        ann = Announcement(
            title="Bad", content="Bad", audience="teams:x,y,z"
        )
        db.session.add(ann)
        db.session.commit()
        assert ann.is_visible_to_user(user) is False
