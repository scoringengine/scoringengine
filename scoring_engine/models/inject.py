import pytz

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Unicode,
    UnicodeText,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Boolean

from scoring_engine.models.base import Base
from scoring_engine.config import config


"""
ID: 5
  State: Draft
  Title: Journey to Mordor
  Scenario: You have the ring, take it to be destroyed!
  Deliverable: Word document in at least 3 volumes with journalistic evidence of each step of your journey and the destruction of the ring.
  Scoring Rubric:
    - 0: Damn hobbitses kept my precious!
    - 50: You gave it your best effort, but died along the way.
    - 100:  You saved the world!
"""


class Template(Base):
    __tablename__ = "template"
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255), nullable=False)
    scenario = Column(UnicodeText, nullable=False)
    deliverable = Column(UnicodeText, nullable=False)
    score = Column(Integer, nullable=False)
    start_time = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    end_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    enabled = Column(Boolean, nullable=False, default=True)

    # Relationships
    # rubric = relationship(
    #     "Rubric", back_populates="template", cascade="all, delete", lazy="joined"
    # )
    inject = relationship(
        "Inject", back_populates="template", cascade="all, delete", lazy="joined"
    )

    def __init__(
        self, title, scenario, deliverable, score, start_time, end_time, enabled=True
    ):
        self.title = title
        self.scenario = scenario
        self.deliverable = deliverable
        self.score = score
        self.start_time = start_time
        self.end_time = end_time
        self.enabled = enabled

    # @property
    # def score(self):
    #     return (
    #         session.query(func.max(Rubric.value))
    #         .filter(Rubric.template_id == self.id)
    #         .scalar()
    #     )

    @property
    def expired(self):
        return datetime.utcnow() > self.end_time

    @property
    def localized_start_time(self):
        return (
            pytz.utc.localize(self.start_time)
            .astimezone(pytz.timezone(config.timezone))
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )

    @property
    def localized_end_time(self):
        return (
            pytz.utc.localize(self.end_time)
            .astimezone(pytz.timezone(config.timezone))
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )


# class Rubric(Base):
#     __tablename__ = "rubric"
#     id = Column(Integer, primary_key=True)
#     deliverable = Column(UnicodeText, nullable=False)
#     value = Column(Integer, nullable=False)

#     # Relationships
#     template_id = Column(Integer, ForeignKey("template.id"))
#     template = relationship("Template", back_populates="rubric")

#     def __init__(self, deliverable, value, template):
#         self.deliverable = deliverable
#         self.value = value
#         self.template = template


"""
Draft
Submitted
Graded

Not Submitted Anything
Have a question waiting for feedback
Submitted waiting for grading
"""


class Inject(Base):
    __tablename__ = "inject"
    id = Column(Integer, primary_key=True)
    score = Column(Integer, default=0)
    status = Column(String(255), default="Draft")
    enabled = Column(Boolean, nullable=False, default=True)
    submitted = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    graded = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    comment = relationship("Comment", back_populates="inject", cascade="all, delete")
    file = relationship("File", back_populates="inject", cascade="all, delete")

    team = relationship("Team", back_populates="inject")
    team_id = Column(Integer, ForeignKey("teams.id"))

    template = relationship("Template", back_populates="inject")
    template_id = Column(Integer, ForeignKey("template.id"))

    def __init__(self, team, template, enabled=True):
        self.team = team
        self.template = template
        self.enabled = enabled


class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    comment = Column(Text, nullable=False)
    time = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    # Relationships
    inject = relationship("Inject", back_populates="comment")
    inject_id = Column(Integer, ForeignKey("inject.id"))
    user = relationship(
        "User", backref="comments", cascade="all, delete-orphan", single_parent=True
    )
    user_id = Column(Integer, ForeignKey("users.id"))

    def __init__(self, comment, user, inject):
        self.comment = comment
        self.user = user
        self.inject = inject


class File(Base):
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

    # Relationships
    inject = relationship("Inject", back_populates="file")
    inject_id = Column(Integer, ForeignKey("inject.id"))
    user = relationship(
        "User", backref="files", cascade="all, delete-orphan", single_parent=True
    )
    user_id = Column(Integer, ForeignKey("users.id"))

    def __init__(self, name, user, inject):
        self.name = name
        self.user = user
        self.inject = inject
