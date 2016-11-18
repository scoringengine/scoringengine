import bcrypt
import OpenSSL
import uuid

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base

from scoring_engine.db import db_salt


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    authenticated = Column(Boolean, default=False)
    session_token = Column(String(40))
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="users")

    def __init__(self, username, password, team=None):
        self.username = username
        self.update_password(password)
        self.team = team

    @property
    def is_red_team(self):
        return self.team.is_red_team

    @property
    def is_white_team(self):
        return self.team.is_white_team

    @property
    def is_blue_team(self):
        return self.team.is_blue_team

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def get_username(self):
        return self.username

    def update_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), db_salt)
        return True

    def get_id(self):
        return str(self.session_token)

    @staticmethod
    def generate_session_token():
        return str(uuid.UUID(bytes=OpenSSL.rand.bytes(16)))

    def __repr__(self):
        return '<User %r>' % self.username
