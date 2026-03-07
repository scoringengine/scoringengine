from datetime import datetime, timedelta, timezone


import pytz

from scoring_engine.models.inject import Inject, InjectComment, InjectFile, InjectRubricScore, RubricItem, Template
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.db import db


def _make_template(session, **overrides):
    """Helper to create a template with sensible defaults."""
    defaults = dict(
        title="Journey to Mordor",
        scenario="You have the ring, take it to be destroyed!",
        deliverable="Word document with evidence",
        start_time=datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
        end_time=datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC),
        enabled=True,
    )
    defaults.update(overrides)
    template = Template(**defaults)
    session.add(template)
    session.commit()
    return template


class TestTemplate:

    def test_init(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        template = Template(
            title="Journey to Mordor",
            scenario="You have the ring, take it to be destroyed!",
            deliverable="Word document with evidence",
            start_time=start_time,
            end_time=end_time,
            enabled=True,
        )
        assert template.title == "Journey to Mordor"
        assert template.scenario == "You have the ring, take it to be destroyed!"
        assert template.deliverable == "Word document with evidence"
        assert template.start_time == start_time
        assert template.end_time == end_time
        assert template.enabled is True

    def test_init_disabled(self):
        template = _make_template(db.session, title="Disabled Inject", enabled=False)
        assert template.enabled is False

    def test_simple_save(self):
        template = _make_template(db.session)
        db.session.commit()
        assert template.id is not None
        assert len(db.session.query(Template).all()) == 1

    def test_max_score_no_rubric_items(self):
        """max_score should be 0 when template has no rubric items."""
        template = _make_template(db.session)
        db.session.commit()
        assert template.max_score == 0

    def test_max_score_with_rubric_items(self):
        """max_score should be the sum of rubric item points."""
        template = _make_template(db.session)
        ri1 = RubricItem(title="Quality", points=60, template=template)
        ri2 = RubricItem(title="Completeness", points=40, template=template)
        db.session.add_all([ri1, ri2])
        db.session.commit()
        assert template.max_score == 100

    def test_expired_property_not_expired(self):
        template = _make_template(
            db.session,
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        db.session.commit()
        assert template.expired is False

    def test_expired_property_expired(self):
        template = _make_template(
            db.session,
            start_time=datetime.now(timezone.utc) - timedelta(hours=4),
            end_time=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        db.session.commit()
        assert template.expired is True

    def test_localized_start_time(self):
        template = _make_template(
            db.session,
            start_time=datetime(2025, 1, 1, 12, 0, 0),
            end_time=datetime(2025, 1, 1, 18, 0, 0),
        )
        db.session.commit()
        localized = template.localized_start_time
        assert isinstance(localized, str)
        assert "2025-01-01" in localized

    def test_localized_end_time(self):
        template = _make_template(
            db.session,
            start_time=datetime(2025, 1, 1, 12, 0, 0),
            end_time=datetime(2025, 1, 1, 18, 0, 0),
        )
        db.session.commit()
        localized = template.localized_end_time
        assert isinstance(localized, str)
        assert "2025-01-01" in localized

    def test_injects_relationship(self):
        team1 = Team(name="Blue Team 1", color="Blue")
        team2 = Team(name="Blue Team 2", color="Blue")
        db.session.add_all([team1, team2])
        template = _make_template(db.session)
        db.session.commit()

        inject1 = Inject(team=team1, template=template)
        inject2 = Inject(team=team2, template=template)
        db.session.add_all([inject1, inject2])
        db.session.commit()

        assert len(template.injects) == 2

    def test_cascade_delete(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        template_id = template.id
        inject_id = inject.id

        db.session.delete(template)
        db.session.commit()

        assert db.session.query(Template).filter_by(id=template_id).first() is None
        assert db.session.query(Inject).filter_by(id=inject_id).first() is None

    def test_rubric_items_relationship(self):
        template = _make_template(db.session)
        ri = RubricItem(title="Quality", points=100, template=template)
        db.session.add(ri)
        db.session.commit()
        assert len(template.rubric_items) == 1
        assert template.rubric_items[0].title == "Quality"

    def test_cascade_delete_rubric_items(self):
        template = _make_template(db.session)
        ri = RubricItem(title="Quality", points=100, template=template)
        db.session.add(ri)
        db.session.commit()
        ri_id = ri.id

        db.session.delete(template)
        db.session.commit()
        assert db.session.query(RubricItem).filter_by(id=ri_id).first() is None


class TestRubricItem:

    def test_init(self):
        template = _make_template(db.session)
        db.session.commit()
        ri = RubricItem(title="Quality", points=60, template=template, description="High quality work", order=1)
        assert ri.title == "Quality"
        assert ri.points == 60
        assert ri.description == "High quality work"
        assert ri.order == 1

    def test_simple_save(self):
        template = _make_template(db.session)
        ri = RubricItem(title="Test", points=50, template=template)
        db.session.add(ri)
        db.session.commit()
        assert ri.id is not None

    def test_default_order(self):
        template = _make_template(db.session)
        ri = RubricItem(title="Test", points=50, template=template)
        db.session.add(ri)
        db.session.commit()
        assert ri.order == 0


class TestInject:

    def test_init(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template, enabled=True)
        assert inject.team == team
        assert inject.template == template
        assert inject.enabled is True

    def test_init_disabled(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template, enabled=False)
        assert inject.enabled is False

    def test_simple_save(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()
        assert inject.id is not None

    def test_default_values(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        assert inject.score == 0  # computed property, no rubric scores
        assert inject.status == "Draft"
        assert inject.enabled is True
        assert inject.submitted is None
        assert inject.graded is None

    def test_score_computed_property(self):
        """score should be computed from rubric scores, not a DB column."""
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        template = _make_template(db.session)
        ri1 = RubricItem(title="Q", points=60, template=template)
        ri2 = RubricItem(title="C", points=40, template=template)
        db.session.add_all([ri1, ri2])
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.flush()

        rs1 = InjectRubricScore(score=50, inject=inject, rubric_item=ri1, grader=None)
        rs2 = InjectRubricScore(score=30, inject=inject, rubric_item=ri2, grader=None)
        db.session.add_all([rs1, rs2])
        db.session.commit()

        assert inject.score == 80

    def test_status_transitions(self):
        """Test all valid status values."""
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        for status in ["Draft", "Submitted", "Revision Requested", "Resubmitted", "Graded"]:
            inject.status = status
            db.session.commit()
            assert inject.status == status

    def test_comments_relationship(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        c1 = InjectComment(content="First comment", user=user, inject=inject)
        c2 = InjectComment(content="Second comment", user=user, inject=inject)
        db.session.add_all([c1, c2])
        db.session.commit()

        assert len(inject.comments) == 2

    def test_same_user_multiple_comments(self):
        """Verify single_parent=True bug is fixed: same user can have multiple comments."""
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        c1 = InjectComment(content="Comment 1", user=user, inject=inject)
        c2 = InjectComment(content="Comment 2", user=user, inject=inject)
        c3 = InjectComment(content="Comment 3", user=user, inject=inject)
        db.session.add_all([c1, c2, c3])
        db.session.commit()

        assert len(inject.comments) == 3

    def test_files_relationship(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        f1 = InjectFile(filename="doc1.pdf", user=user, inject=inject)
        f2 = InjectFile(filename="doc2.pdf", user=user, inject=inject)
        db.session.add_all([f1, f2])
        db.session.commit()

        assert len(inject.files) == 2

    def test_same_user_multiple_files(self):
        """Verify single_parent=True bug is fixed: same user can upload multiple files."""
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        for i in range(5):
            db.session.add(InjectFile(filename=f"file{i}.pdf", user=user, inject=inject))
        db.session.commit()

        assert len(inject.files) == 5

    def test_cascade_delete_comments_files_scores(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        ri = RubricItem(title="Q", points=100, template=template)
        db.session.add(ri)
        db.session.commit()

        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.flush()

        comment = InjectComment(content="Test", user=user, inject=inject)
        file_obj = InjectFile(filename="test.pdf", user=user, inject=inject)
        score = InjectRubricScore(score=80, inject=inject, rubric_item=ri, grader=None)
        db.session.add_all([comment, file_obj, score])
        db.session.commit()

        inject_id = inject.id
        db.session.delete(inject)
        db.session.commit()

        assert db.session.query(Inject).filter_by(id=inject_id).first() is None
        assert db.session.query(InjectComment).filter_by(inject_id=inject_id).first() is None
        assert db.session.query(InjectFile).filter_by(inject_id=inject_id).first() is None
        assert db.session.query(InjectRubricScore).filter_by(inject_id=inject_id).first() is None


class TestInjectRubricScore:

    def test_init(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        template = _make_template(db.session)
        ri = RubricItem(title="Q", points=100, template=template)
        db.session.add(ri)
        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        score = InjectRubricScore(score=80, inject=inject, rubric_item=ri, grader=None)
        db.session.add(score)
        db.session.commit()

        assert score.id is not None
        assert score.score == 80
        assert score.inject == inject
        assert score.rubric_item == ri

    def test_with_grader(self):
        team = Team(name="White Team", color="White")
        db.session.add(team)
        user = User(username="grader", password="testpass", team=team)
        db.session.add(user)
        blue_team = Team(name="Blue", color="Blue")
        db.session.add(blue_team)
        template = _make_template(db.session)
        ri = RubricItem(title="Q", points=100, template=template)
        db.session.add(ri)
        inject = Inject(team=blue_team, template=template)
        db.session.add(inject)
        db.session.commit()

        score = InjectRubricScore(score=90, inject=inject, rubric_item=ri, grader=user)
        db.session.add(score)
        db.session.commit()

        assert score.grader == user


class TestInjectComment:

    def test_init(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        comment = InjectComment(content="This is a test comment", user=user, inject=inject)
        assert comment.content == "This is a test comment"
        assert comment.user == user
        assert comment.inject == inject

    def test_simple_save(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        comment = InjectComment(content="Test comment", user=user, inject=inject)
        db.session.add(comment)
        db.session.commit()
        assert comment.id is not None

    def test_default_is_read(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        comment = InjectComment(content="Test", user=user, inject=inject)
        db.session.add(comment)
        db.session.commit()

        assert comment.is_read is False
        assert comment.created is not None

    def test_mark_as_read(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        comment = InjectComment(content="Test", user=user, inject=inject)
        db.session.add(comment)
        db.session.commit()

        comment.is_read = True
        db.session.commit()
        assert comment.is_read is True


class TestInjectFile:

    def test_init(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        file_obj = InjectFile(filename="evidence.pdf", user=user, inject=inject)
        assert file_obj.filename == "evidence.pdf"
        assert file_obj.user == user
        assert file_obj.inject == inject

    def test_original_filename(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        file_obj = InjectFile(
            filename="Inject1_BlueTeam_evidence.pdf", user=user, inject=inject, original_filename="evidence.pdf"
        )
        db.session.add(file_obj)
        db.session.commit()
        assert file_obj.original_filename == "evidence.pdf"

    def test_simple_save(self):
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        template = _make_template(db.session)
        inject = Inject(team=team, template=template)
        db.session.add(inject)
        db.session.commit()

        file_obj = InjectFile(filename="test.docx", user=user, inject=inject)
        db.session.add(file_obj)
        db.session.commit()
        assert file_obj.id is not None
