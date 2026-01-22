import pytest
from datetime import datetime, timedelta, timezone
import pytz

from scoring_engine.models.inject import Template, Inject, Comment, File
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

from tests.scoring_engine.unit_test import UnitTest


class TestTemplate(UnitTest):

    def test_init(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Journey to Mordor",
            scenario="You have the ring, take it to be destroyed!",
            deliverable="Word document with evidence",
            score=100,
            start_time=start_time,
            end_time=end_time,
            enabled=True
        )
        assert template.title == "Journey to Mordor"
        assert template.scenario == "You have the ring, take it to be destroyed!"
        assert template.deliverable == "Word document with evidence"
        assert template.score == 100
        assert template.start_time == start_time
        assert template.end_time == end_time
        assert template.enabled is True

    def test_init_disabled(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Disabled Inject",
            scenario="This is disabled",
            deliverable="Nothing",
            score=50,
            start_time=start_time,
            end_time=end_time,
            enabled=False
        )
        assert template.enabled is False

    def test_simple_save(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test scenario",
            deliverable="Test deliverable",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()
        assert template.id is not None
        assert len(self.session.query(Template).all()) == 1

    def test_expired_property_not_expired(self):
        """Test that expired property returns False for ongoing template"""
        start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        end_time = datetime.now(timezone.utc) + timedelta(hours=2)
        template = Template(
            title="Active Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()
        assert template.expired is False

    def test_expired_property_expired(self):
        """Test that expired property returns True for past template"""
        start_time = datetime.now(timezone.utc) - timedelta(hours=4)
        end_time = datetime.now(timezone.utc) - timedelta(hours=2)
        template = Template(
            title="Expired Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()
        assert template.expired is True

    def test_localized_start_time(self):
        """Test that start_time is properly localized"""
        start_time = datetime(2025, 1, 1, 12, 0, 0)  # Naive datetime
        end_time = datetime(2025, 1, 1, 18, 0, 0)
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()

        localized = template.localized_start_time
        assert isinstance(localized, str)
        assert "2025-01-01" in localized
        assert any(tz in localized for tz in ["UTC", "EST", "PST", "MST", "CST"])

    def test_localized_end_time(self):
        """Test that end_time is properly localized"""
        start_time = datetime(2025, 1, 1, 12, 0, 0)
        end_time = datetime(2025, 1, 1, 18, 0, 0)
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()

        localized = template.localized_end_time
        assert isinstance(localized, str)
        assert "2025-01-01" in localized

    def test_inject_relationship(self):
        """Test that Template can have multiple Injects"""
        team1 = Team(name="Blue Team 1", color="Blue")
        team2 = Team(name="Blue Team 2", color="Blue")
        self.session.add(team1)
        self.session.add(team2)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()

        inject1 = Inject(team=team1, template=template)
        inject2 = Inject(team=team2, template=template)
        self.session.add(inject1)
        self.session.add(inject2)
        self.session.commit()

        assert len(template.inject) == 2

    def test_cascade_delete(self):
        """Test that deleting a Template cascades to delete Injects"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        template_id = template.id
        inject_id = inject.id

        # Delete template
        self.session.delete(template)
        self.session.commit()

        # Inject should be deleted too
        assert self.session.query(Template).filter_by(id=template_id).first() is None
        assert self.session.query(Inject).filter_by(id=inject_id).first() is None


class TestInject(UnitTest):

    def test_init(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()

        inject = Inject(team=team, template=template, enabled=True)
        assert inject.team == team
        assert inject.template == template
        assert inject.enabled is True
        # Defaults like status and score are applied by database on commit, not in __init__

    def test_init_disabled(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()

        inject = Inject(team=team, template=template, enabled=False)
        assert inject.enabled is False

    def test_simple_save(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()
        assert inject.id is not None
        assert len(self.session.query(Inject).all()) == 1

    def test_default_values(self):
        """Test that default values are set correctly after commit"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)
        self.session.commit()

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        # After commit, database defaults are applied
        assert inject.score == 0
        assert inject.status == "Draft"
        assert inject.enabled is True
        assert inject.submitted is not None
        assert inject.graded is not None

    def test_status_draft(self):
        """Test inject in Draft status"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        assert inject.status == "Draft"

    def test_status_submitted(self):
        """Test changing inject status to Submitted"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        inject.status = "Submitted"
        inject.submitted = datetime.now(timezone.utc)
        self.session.commit()

        assert inject.status == "Submitted"

    def test_status_graded(self):
        """Test changing inject status to Graded with score"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        inject.status = "Graded"
        inject.score = 85
        inject.graded = datetime.now(timezone.utc)
        self.session.commit()

        assert inject.status == "Graded"
        assert inject.score == 85

    def test_comment_relationship(self):
        """Test that Inject can have multiple Comments"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user1 = User(username="testuser1", password="testpass", team=team)
        user2 = User(username="testuser2", password="testpass", team=team)
        self.session.add(user1)
        self.session.add(user2)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        # Use different users due to single_parent=True constraint
        comment1 = Comment(comment="First comment", user=user1, inject=inject)
        comment2 = Comment(comment="Second comment", user=user2, inject=inject)
        self.session.add(comment1)
        self.session.add(comment2)
        self.session.commit()

        assert len(inject.comment) == 2

    def test_file_relationship(self):
        """Test that Inject can have multiple Files"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user1 = User(username="testuser1", password="testpass", team=team)
        user2 = User(username="testuser2", password="testpass", team=team)
        self.session.add(user1)
        self.session.add(user2)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        # Use different users due to single_parent=True constraint
        file1 = File(name="document1.pdf", user=user1, inject=inject)
        file2 = File(name="evidence.docx", user=user2, inject=inject)
        self.session.add(file1)
        self.session.add(file2)
        self.session.commit()

        assert len(inject.file) == 2

    def test_cascade_delete_comments_and_files(self):
        """Test that deleting an Inject cascades to delete Comments and Files"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        comment = Comment(comment="Test comment", user=user, inject=inject)
        file = File(name="test.pdf", user=user, inject=inject)
        self.session.add(comment)
        self.session.add(file)
        self.session.commit()

        inject_id = inject.id
        comment_id = comment.id
        file_id = file.id

        # Delete inject
        self.session.delete(inject)
        self.session.commit()

        # Comments and Files should be deleted too
        assert self.session.query(Inject).filter_by(id=inject_id).first() is None
        assert self.session.query(Comment).filter_by(id=comment_id).first() is None
        assert self.session.query(File).filter_by(id=file_id).first() is None


class TestComment(UnitTest):

    def test_init(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        comment = Comment(comment="This is a test comment", user=user, inject=inject)
        assert comment.comment == "This is a test comment"
        assert comment.user == user
        assert comment.inject == inject
        # Default is applied by database on commit

    def test_simple_save(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        comment = Comment(comment="Test comment", user=user, inject=inject)
        self.session.add(comment)
        self.session.commit()
        assert comment.id is not None
        assert len(self.session.query(Comment).all()) == 1

    def test_default_is_read(self):
        """Test that is_read defaults to False after commit"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        comment = Comment(comment="Test", user=user, inject=inject)
        self.session.add(comment)
        self.session.commit()

        # Database applies default after commit
        assert comment.is_read is False
        assert comment.time is not None

    def test_mark_as_read(self):
        """Test marking a comment as read"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        comment = Comment(comment="Test", user=user, inject=inject)
        self.session.add(comment)
        self.session.commit()

        comment.is_read = True
        self.session.commit()

        assert comment.is_read is True

    def test_user_relationship(self):
        """Test that Comment has proper relationship to User"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        comment = Comment(comment="Test", user=user, inject=inject)
        self.session.add(comment)
        self.session.commit()

        # Access comment through user relationship
        assert len(user.comments) == 1
        assert user.comments[0].comment == "Test"


class TestFile(UnitTest):

    def test_init(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        file = File(name="evidence.pdf", user=user, inject=inject)
        assert file.name == "evidence.pdf"
        assert file.user == user
        assert file.inject == inject

    def test_simple_save(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        file = File(name="test.docx", user=user, inject=inject)
        self.session.add(file)
        self.session.commit()
        assert file.id is not None
        assert len(self.session.query(File).all()) == 1

    def test_multiple_files(self):
        """Test that multiple files can be added to an inject"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user1 = User(username="testuser1", password="testpass", team=team)
        user2 = User(username="testuser2", password="testpass", team=team)
        user3 = User(username="testuser3", password="testpass", team=team)
        self.session.add(user1)
        self.session.add(user2)
        self.session.add(user3)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        # Use different users due to single_parent=True constraint
        file1 = File(name="doc1.pdf", user=user1, inject=inject)
        file2 = File(name="doc2.pdf", user=user2, inject=inject)
        file3 = File(name="screenshot.png", user=user3, inject=inject)
        self.session.add(file1)
        self.session.add(file2)
        self.session.add(file3)
        self.session.commit()

        assert len(self.session.query(File).all()) == 3

    def test_user_relationship(self):
        """Test that File has proper relationship to User"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Test Template",
            scenario="Test",
            deliverable="Test",
            score=100,
            start_time=start_time,
            end_time=end_time
        )
        self.session.add(template)

        inject = Inject(team=team, template=template)
        self.session.add(inject)
        self.session.commit()

        file = File(name="test.pdf", user=user, inject=inject)
        self.session.add(file)
        self.session.commit()

        # Access file through user relationship
        assert len(user.files) == 1
        assert user.files[0].name == "test.pdf"
