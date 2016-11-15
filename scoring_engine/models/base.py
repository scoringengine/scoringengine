from sqlalchemy.ext.declarative import declarative_base
from scoring_engine.db import db

Base = declarative_base()
Base.query = db.session.query_property()
