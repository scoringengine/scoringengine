import datetime

from scoring_engine.models.announcement import Announcement, AnnouncementRead
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

from tests.scoring_engine.unit_test import UnitTest


class TestAnnouncement(UnitTest):

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
        self.session.add(ann)
        self.session.commit()
        assert ann.id is not None
        assert ann.created_at is not None

    def test_defaults(self):
        """Test that defaults are applied after commit"""
        ann = Announcement(title="Defaults", content="Check defaults")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_pinned is False
        assert ann.is_active is True
        assert ann.expires_at is None

    def test_to_dict(self):
        """Test serialization to dictionary"""
        ann = Announcement(title="Dict", content="<p>Body</p>")
        self.session.add(ann)
        self.session.commit()
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
        self.session.add(team)
        user = User(username="admin", password="pass", team=team)
        self.session.add(user)
        self.session.commit()
        ann = Announcement(
            title="Authored",
            content="Test",
            author_id=user.id,
        )
        self.session.add(ann)
        self.session.commit()
        d = ann.to_dict()
        assert d["author_name"] == "admin"
        assert d["author_id"] == user.id

    # --- Visibility: Global ---

    def test_global_visible_to_unauthenticated(self):
        """Global announcements are visible to everyone"""
        ann = Announcement(title="G", content="Global", audience="global")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(None) is True

    def test_global_visible_to_blue(self):
        team = Team(name="Blue 1", color="Blue")
        self.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        self.session.add(user)
        self.session.commit()
        ann = Announcement(title="G", content="Global")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user) is True

    # --- Visibility: all_blue ---

    def test_all_blue_visible_to_blue_team(self):
        team = Team(name="Blue 1", color="Blue")
        self.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        self.session.add(user)
        self.session.commit()
        ann = Announcement(title="B", content="Blue", audience="all_blue")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user) is True

    def test_all_blue_hidden_from_red_team(self):
        team = Team(name="Red Team", color="Red")
        self.session.add(team)
        user = User(username="r1", password="p", team=team)
        user.authenticated = True
        self.session.add(user)
        self.session.commit()
        ann = Announcement(title="B", content="Blue", audience="all_blue")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user) is False

    def test_all_blue_hidden_from_unauthenticated(self):
        ann = Announcement(title="B", content="Blue", audience="all_blue")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(None) is False

    # --- Visibility: all_red ---

    def test_all_red_visible_to_red_team(self):
        team = Team(name="Red Team", color="Red")
        self.session.add(team)
        user = User(username="r1", password="p", team=team)
        user.authenticated = True
        self.session.add(user)
        self.session.commit()
        ann = Announcement(title="R", content="Red", audience="all_red")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user) is True

    def test_all_red_hidden_from_blue_team(self):
        team = Team(name="Blue 1", color="Blue")
        self.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        self.session.add(user)
        self.session.commit()
        ann = Announcement(title="R", content="Red", audience="all_red")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user) is False

    def test_all_red_hidden_from_unauthenticated(self):
        ann = Announcement(title="R", content="Red", audience="all_red")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(None) is False

    # --- Visibility: team:ID ---

    def test_team_specific_visible_to_correct_team(self):
        team = Team(name="Blue 1", color="Blue")
        self.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        self.session.add(user)
        self.session.commit()
        ann = Announcement(
            title="T",
            content="Team",
            audience=f"team:{team.id}",
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user) is True

    def test_team_specific_hidden_from_other_team(self):
        team1 = Team(name="Blue 1", color="Blue")
        team2 = Team(name="Blue 2", color="Blue")
        self.session.add_all([team1, team2])
        self.session.commit()
        user2 = User(username="b2", password="p", team=team2)
        user2.authenticated = True
        self.session.add(user2)
        self.session.commit()
        ann = Announcement(
            title="T",
            content="Team",
            audience=f"team:{team1.id}",
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user2) is False

    def test_team_specific_hidden_from_unauthenticated(self):
        ann = Announcement(title="T", content="Team", audience="team:1")
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(None) is False

    # --- Visibility: teams:1,3,5 ---

    def test_multi_team_visible_to_included_team(self):
        team1 = Team(name="Blue 1", color="Blue")
        team2 = Team(name="Blue 2", color="Blue")
        team3 = Team(name="Blue 3", color="Blue")
        self.session.add_all([team1, team2, team3])
        self.session.commit()
        user1 = User(username="b1", password="p", team=team1)
        user1.authenticated = True
        user3 = User(username="b3", password="p", team=team3)
        user3.authenticated = True
        self.session.add_all([user1, user3])
        self.session.commit()
        audience = f"teams:{team1.id},{team3.id}"
        ann = Announcement(
            title="M",
            content="Multi",
            audience=audience,
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user1) is True
        assert ann.is_visible_to_user(user3) is True

    def test_multi_team_hidden_from_excluded_team(self):
        team1 = Team(name="Blue 1", color="Blue")
        team2 = Team(name="Blue 2", color="Blue")
        self.session.add_all([team1, team2])
        self.session.commit()
        user2 = User(username="b2", password="p", team=team2)
        user2.authenticated = True
        self.session.add(user2)
        self.session.commit()
        ann = Announcement(
            title="M",
            content="Multi",
            audience=f"teams:{team1.id}",
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user2) is False

    # --- Visibility: white team sees all ---

    def test_white_team_sees_team_specific(self):
        white = Team(name="White Team", color="White")
        blue = Team(name="Blue 1", color="Blue")
        self.session.add_all([white, blue])
        self.session.commit()
        admin = User(username="admin", password="p", team=white)
        admin.authenticated = True
        self.session.add(admin)
        self.session.commit()
        ann = Announcement(
            title="T",
            content="Team",
            audience=f"team:{blue.id}",
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(admin) is True

    def test_white_team_sees_all_blue(self):
        white = Team(name="White Team", color="White")
        self.session.add(white)
        admin = User(username="admin", password="p", team=white)
        admin.authenticated = True
        self.session.add(admin)
        self.session.commit()
        ann = Announcement(
            title="B",
            content="Blue",
            audience="all_blue",
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(admin) is True

    # --- Visibility: inactive / expired ---

    def test_inactive_hidden(self):
        ann = Announcement(title="I", content="Inactive")
        ann.is_active = False
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(None) is False

    def test_expired_hidden(self):
        ann = Announcement(title="E", content="Expired")
        ann.expires_at = datetime.datetime.utcnow() - datetime.timedelta(
            hours=1
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(None) is False

    def test_future_expiry_visible(self):
        ann = Announcement(title="F", content="Future")
        ann.expires_at = datetime.datetime.utcnow() + datetime.timedelta(
            hours=1
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(None) is True

    # --- Bad audience values ---

    def test_bad_team_id_hidden(self):
        team = Team(name="Blue 1", color="Blue")
        self.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        self.session.add(user)
        self.session.commit()
        ann = Announcement(
            title="Bad", content="Bad", audience="team:notanumber"
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user) is False

    def test_bad_teams_value_hidden(self):
        team = Team(name="Blue 1", color="Blue")
        self.session.add(team)
        user = User(username="b1", password="p", team=team)
        user.authenticated = True
        self.session.add(user)
        self.session.commit()
        ann = Announcement(
            title="Bad", content="Bad", audience="teams:x,y,z"
        )
        self.session.add(ann)
        self.session.commit()
        assert ann.is_visible_to_user(user) is False


class TestAnnouncementRead(UnitTest):

    def _make_user(self):
        team = Team(name="Blue 1", color="Blue")
        self.session.add(team)
        user = User(username="b1", password="p", team=team)
        self.session.add(user)
        self.session.commit()
        return user

    def _make_announcement(self, title="Test"):
        ann = Announcement(title=title, content="Content")
        self.session.add(ann)
        self.session.commit()
        return ann

    def test_init(self):
        """Test creating an announcement read record"""
        user = self._make_user()
        ann = self._make_announcement()
        read = AnnouncementRead(user_id=user.id, announcement_id=ann.id)
        self.session.add(read)
        self.session.commit()
        assert read.id is not None
        assert read.user_id == user.id
        assert read.announcement_id == ann.id
        assert read.read_at is not None

    def test_is_read_false(self):
        """Test is_read returns False for unread announcement"""
        user = self._make_user()
        ann = self._make_announcement()
        assert AnnouncementRead.is_read(self.session, user.id, ann.id) is False

    def test_is_read_true(self):
        """Test is_read returns True after marking as read"""
        user = self._make_user()
        ann = self._make_announcement()
        AnnouncementRead.mark_as_read(self.session, user.id, ann.id)
        assert AnnouncementRead.is_read(self.session, user.id, ann.id) is True

    def test_get_read_announcement_ids_empty(self):
        """Test get_read_announcement_ids returns empty set initially"""
        user = self._make_user()
        ids = AnnouncementRead.get_read_announcement_ids(self.session, user.id)
        assert ids == set()

    def test_get_read_announcement_ids(self):
        """Test get_read_announcement_ids returns correct IDs"""
        user = self._make_user()
        ann1 = self._make_announcement("A1")
        ann2 = self._make_announcement("A2")
        ann3 = self._make_announcement("A3")
        AnnouncementRead.mark_as_read(self.session, user.id, ann1.id)
        AnnouncementRead.mark_as_read(self.session, user.id, ann3.id)
        ids = AnnouncementRead.get_read_announcement_ids(self.session, user.id)
        assert ids == {ann1.id, ann3.id}

    def test_mark_as_read_creates_record(self):
        """Test mark_as_read creates a new read record"""
        user = self._make_user()
        ann = self._make_announcement()
        read = AnnouncementRead.mark_as_read(self.session, user.id, ann.id)
        assert read.id is not None
        assert read.user_id == user.id
        assert read.announcement_id == ann.id

    def test_mark_as_read_idempotent(self):
        """Test marking the same announcement as read twice returns existing record"""
        user = self._make_user()
        ann = self._make_announcement()
        read1 = AnnouncementRead.mark_as_read(self.session, user.id, ann.id)
        read2 = AnnouncementRead.mark_as_read(self.session, user.id, ann.id)
        assert read1.id == read2.id

    def test_mark_many_as_read(self):
        """Test marking multiple announcements as read at once"""
        user = self._make_user()
        ann1 = self._make_announcement("A1")
        ann2 = self._make_announcement("A2")
        ann3 = self._make_announcement("A3")
        AnnouncementRead.mark_many_as_read(
            self.session, user.id, [ann1.id, ann2.id, ann3.id]
        )
        ids = AnnouncementRead.get_read_announcement_ids(self.session, user.id)
        assert ids == {ann1.id, ann2.id, ann3.id}

    def test_mark_many_as_read_skips_already_read(self):
        """Test mark_many_as_read doesn't duplicate existing records"""
        user = self._make_user()
        ann1 = self._make_announcement("A1")
        ann2 = self._make_announcement("A2")
        # Mark ann1 first
        AnnouncementRead.mark_as_read(self.session, user.id, ann1.id)
        # Now mark both
        AnnouncementRead.mark_many_as_read(
            self.session, user.id, [ann1.id, ann2.id]
        )
        ids = AnnouncementRead.get_read_announcement_ids(self.session, user.id)
        assert ids == {ann1.id, ann2.id}
        # Only 2 records total, not 3
        count = (
            self.session.query(AnnouncementRead)
            .filter(AnnouncementRead.user_id == user.id)
            .count()
        )
        assert count == 2

    def test_per_user_isolation(self):
        """Test that read status is tracked per user"""
        team = Team(name="Blue 1", color="Blue")
        self.session.add(team)
        user1 = User(username="u1", password="p", team=team)
        user2 = User(username="u2", password="p", team=team)
        self.session.add_all([user1, user2])
        self.session.commit()
        ann = self._make_announcement()
        AnnouncementRead.mark_as_read(self.session, user1.id, ann.id)
        assert AnnouncementRead.is_read(self.session, user1.id, ann.id) is True
        assert AnnouncementRead.is_read(self.session, user2.id, ann.id) is False
