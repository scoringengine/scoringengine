from sqlalchemy.ext.declarative.api import DeclarativeMeta
from scoring_engine.models.base import Base


class TestBase(object):

    def test_base_class(self):
        assert isinstance(Base, DeclarativeMeta)
