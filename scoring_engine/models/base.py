from dictalchemy import make_class_dictable

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
make_class_dictable(Base)
