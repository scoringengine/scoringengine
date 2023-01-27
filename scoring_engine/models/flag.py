from sqlalchemy import Column, Enum, Integer, PickleType
# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from datetime import datetime
import pytz

import html

# import uuid

from scoring_engine.models.base import Base
from scoring_engine.config import config


import enum
class FlagTypeEnum(enum.Enum):
    file = 'file'
    pipe = 'pipe'
    net = 'net'
    reg = 'reg'


class Flag(Base):
    __tablename__ = 'flags'
    id = Column(Integer, primary_key=True)
    type = Column(Enum, default="")
    data = Column(PickleType, default="")