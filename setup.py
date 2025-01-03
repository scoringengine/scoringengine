try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    "description": "Scoring Engine for Red/White/Blue Team Competitions",
    "author": "Brandon Myers, Rusty Bower, Zack Allen",
    "url": "https://github.com/scoringengine/scoringengine",
    "download_url": "https://github.com/scoringengine/scoringengine/archive/master.zip",
    "author_email": "pwnbus@mozilla.com, rusty@rustybower.com, zallen@fastly.com",
    "version": "1.0.0",
    "install_requires": [
        "bcrypt==3.1.3",
        # 'billiard==3.5.0.4',
        # 'celery==4.2.2',
        "celery[redis]==5.2.7",
        "configparser==3.5.0",
        "Flask==2.3.2",
        "Flask-Caching==1.10.1",
        "Flask-Login==0.6.2",
        "Flask-SQLAlchemy==2.5.1",
        "Flask-WTF==1.1.1",
        # "itsdangerous==1.1.0",
        # "markupsafe==1.1.1",
        "mysqlclient==2.1.0",
        "pynsive==0.2.7",
        "python-dateutil==2.8.2",
        "PyYAML==6.0.2",
        "ranking==0.3.2",
        # 'redis==4.3.4',
        "shellescape==3.4.1",
        "Werkzeug==2.3.6",
        "uWSGI==2.0.28",
    ],
    "packages": ["scoring_engine"],
    "scripts": [],
    "name": "scoring_engine",
}

setup(**config)
