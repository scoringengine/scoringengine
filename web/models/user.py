import bcrypt
from sqlalchemy import Boolean, Column, Integer, String
from web.database import Model


class User(Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False)
    password = Column(String(50), nullable=False)
    authenticated = Column(Boolean, default=False)

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<User %r>' % self.username
