import bcrypt
import secrets

from flask_login import UserMixin

from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base
from scoring_engine.models.team import Team

from scoring_engine.db import db_salt, session


class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    token = Column(String(64))
    authenticated = Column(Boolean, default=False)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship('Team', back_populates='users')

    def __init__(self, username, password, team=None):
        self.username = username
        self.update_password(password)
        self.token = secrets.token_hex(32)
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
        return self.authenticated

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def get_username(self):
        return self.username

    def check_password(self, password):
        # this is due to some weird bug between rusty and I
        # where his env was returning a str, and mine were bytes
        if isinstance(password, str):
            password = password.encode('utf-8')
        return bcrypt.checkpw(password, self.password.encode('utf-8'))

    def update_password(self, password):
        self.password = User.generate_hash(password)
        return True

    @staticmethod
    def get_all_red_users():
        return session.query(User).join(Team).filter(Team.color == 'Red').all()

    @staticmethod
    def generate_hash(password, salt=None):
        if salt is None:
            salt = db_salt
        elif isinstance(salt, str):
            salt = salt.encode('utf-8')

        # this is due to some weird bug between rusty and I
        # where his env was returning a str, and mine were bytes
        if isinstance(password, str):
            password = password.encode('utf-8')
        return bcrypt.hashpw(password, salt).decode('utf-8')

    def get_id(self):
        return self.id
