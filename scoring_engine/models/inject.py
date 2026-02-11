from datetime import datetime, timezone

import pytz
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Unicode, UnicodeText
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Boolean

from scoring_engine.config import config
from scoring_engine.models.base import Base


def _ensure_utc_aware(dt):
    """Ensure datetime is timezone-aware in UTC. Handles both naive and aware datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return pytz.utc.localize(dt)
    return dt.astimezone(pytz.utc)



class Template(Base):
    __tablename__ = "template"
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255), nullable=False)
    scenario = Column(UnicodeText, nullable=False)
    deliverable = Column(UnicodeText, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    enabled = Column(Boolean, nullable=False, default=True)

    # Relationships
    injects = relationship("Inject", back_populates="template", cascade="all, delete", lazy="joined")
    rubric_items = relationship(
        "RubricItem", back_populates="template", cascade="all, delete", lazy="joined", order_by="RubricItem.order"
    )

    def __init__(self, title, scenario, deliverable, start_time, end_time, enabled=True):
        self.title = title
        self.scenario = scenario
        self.deliverable = deliverable
        self.start_time = start_time
        self.end_time = end_time
        self.enabled = enabled

    @property
    def max_score(self):
        """Sum of all rubric item points for this template."""
        return sum(item.points for item in self.rubric_items)

    @property
    def expired(self):
        now = datetime.now(timezone.utc)
        end = self.end_time
        if end.tzinfo is None:
            now = now.replace(tzinfo=None)
        return now > end

    @property
    def localized_start_time(self):
        return (
            _ensure_utc_aware(self.start_time)
            .astimezone(pytz.timezone(config.timezone))
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )

    @property
    def localized_end_time(self):
        return (
            _ensure_utc_aware(self.end_time).astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")
        )


class RubricItem(Base):
    __tablename__ = "rubric_item"
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText, nullable=True)
    points = Column(Integer, nullable=False)
    order = Column(Integer, default=0)

    # Relationships
    template_id = Column(Integer, ForeignKey("template.id"))
    template = relationship("Template", back_populates="rubric_items")

    def __init__(self, title, points, template, description=None, order=0):
        self.title = title
        self.points = points
        self.template = template
        self.description = description
        self.order = order


class Inject(Base):
    __tablename__ = "inject"
    id = Column(Integer, primary_key=True)
    status = Column(String(255), default="Draft")
    enabled = Column(Boolean, nullable=False, default=True)
    submitted = Column(DateTime(timezone=True), nullable=True)
    graded = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    comments = relationship("InjectComment", back_populates="inject", cascade="all, delete")
    files = relationship("InjectFile", back_populates="inject", cascade="all, delete")
    rubric_scores = relationship("InjectRubricScore", back_populates="inject", cascade="all, delete")

    team = relationship("Team", back_populates="injects")
    team_id = Column(Integer, ForeignKey("teams.id"))

    template = relationship("Template", back_populates="injects")
    template_id = Column(Integer, ForeignKey("template.id"))

    def __init__(self, team, template, enabled=True):
        self.team = team
        self.template = template
        self.enabled = enabled

    @property
    def score(self):
        """Sum of all rubric scores for this inject."""
        return sum(rs.score for rs in self.rubric_scores)


class InjectRubricScore(Base):
    __tablename__ = "inject_rubric_score"
    id = Column(Integer, primary_key=True)
    score = Column(Integer, nullable=False)

    # Relationships
    inject_id = Column(Integer, ForeignKey("inject.id"))
    inject = relationship("Inject", back_populates="rubric_scores")

    rubric_item_id = Column(Integer, ForeignKey("rubric_item.id"))
    rubric_item = relationship("RubricItem")

    grader_id = Column(Integer, ForeignKey("users.id"))
    grader = relationship("User")

    def __init__(self, score, inject, rubric_item, grader):
        self.score = score
        self.inject = inject
        self.rubric_item = rubric_item
        self.grader = grader


class InjectComment(Base):
    __tablename__ = "inject_comment"
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_read = Column(Boolean, default=False)

    # Relationships
    inject = relationship("Inject", back_populates="comments")
    inject_id = Column(Integer, ForeignKey("inject.id"))
    user = relationship("User", foreign_keys="InjectComment.user_id")
    user_id = Column(Integer, ForeignKey("users.id"))

    def __init__(self, content, user, inject):
        self.content = content
        self.user = user
        self.inject = inject


class InjectFile(Base):
    __tablename__ = "inject_file"
    id = Column(Integer, primary_key=True)
    filename = Column(Text, nullable=False)
    original_filename = Column(Text, nullable=True)
    uploaded = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    inject = relationship("Inject", back_populates="files")
    inject_id = Column(Integer, ForeignKey("inject.id"))
    user = relationship("User", foreign_keys="InjectFile.user_id")
    user_id = Column(Integer, ForeignKey("users.id"))

    def __init__(self, filename, user, inject, original_filename=None):
        self.filename = filename
        self.user = user
        self.inject = inject
        self.original_filename = original_filename
