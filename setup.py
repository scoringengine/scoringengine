try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# from scoring_engine.version import version

config = {
    "description": "Scoring Engine for Red/White/Blue Team Competitions",
    "author": "Brandon Myers, Rusty Bower, Zack Allen",
    "url": "https://github.com/scoringengine/scoringengine",
    "download_url": "https://github.com/scoringengine/scoringengine/archive/master.zip",
    "author_email": "pwnbus@mozilla.com, rusty@rustybower.com, zallen@fastly.com",
    # 'version': version,
    "install_requires": [
        "bcrypt==3.2.0",
        "celery==4.4.7",
        "configparser==3.5.0",
        "Flask==1.1.4",
        "Flask-Caching==1.10.1",
        "Flask-Login==0.5.0",
        "Flask-SQLAlchemy==2.5.1",
        "Flask-WTF==0.15.1",
        "mysqlclient==2.1.0",
        "pynsive==0.2.7",
        "PyYAML==5.4.1",
        "redis==3.5.3",
        "shellescape==3.8.1",
        "Werkzeug==0.16.1",
        "uWSGI==2.0.20",
    ],
    "packages": ["scoring_engine"],
    "scripts": [],
    "name": "scoring_engine",
}

setup(**config)
