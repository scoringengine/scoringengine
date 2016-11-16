import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.base import Base

from sqlalchemy.ext.declarative.api import DeclarativeMeta


class TestBase(object):

    def test_base_class(self):
        assert isinstance(Base, DeclarativeMeta)
