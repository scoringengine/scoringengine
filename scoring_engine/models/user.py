import bcrypt
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base

from scoring_engine.db import db_salt


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False)
    password = Column(String(50), nullable=False)
    authenticated = Column(Boolean, default=False)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="users")

    def __init__(self, username, password, team=None):
        self.username = username
        self.password = self.update_password(password)
        self.team = team

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
        return str(self.id)  # python 3

    def __repr__(self):
        return '<User %r>' % self.username
