from scoring_engine.db import db

# For backward compatibility, export db.Model as Base
# This allows models to inherit from Base while using Flask-SQLAlchemy
Base = db.Model
