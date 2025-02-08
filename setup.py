from setuptools import setup

config = {
    "description": "Scoring Engine for Red/White/Blue Team Competitions",
    "author": "Brandon Myers, Rusty Bower, Zack Allen",
    "url": "https://github.com/scoringengine/scoringengine",
    "download_url": "https://github.com/scoringengine/scoringengine/archive/master.zip",
    "author_email": "pwnbus@mozilla.com, rusty@rustybower.com, zallen@fastly.com",
    "version": "1.0.0",
    "install_requires": [
        "bcrypt==4.2.1",
        # 'billiard==3.5.0.4',
        # 'celery==4.2.2',
        "celery[redis]==5.4",
        "configparser==7.1.0",
        "Flask==3.1.0",
        "Flask-Caching==2.3.0",
        "Flask-Login==0.6.3",
        "Flask-SQLAlchemy==3.1.1",
        "Flask-WTF==1.2.2",
        # "itsdangerous==1.1.0",
        # "markupsafe==1.1.1",
        "mysqlclient==2.1.0",
        # "pynsive==0.2.7",
        "python-dateutil==2.9.0.post0",
        "pytz==2025.1",
        "PyYAML==6.0.2",
        "ranking==0.3.2",
        # 'redis==4.3.4',
        "Werkzeug==3.1.3",
        "uWSGI==2.0.28",
    ],
    "packages": ["scoring_engine"],
    "scripts": [],
    "name": "scoring_engine",
}

setup(**config)
