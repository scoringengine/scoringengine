try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from scoring_engine.version import version

config = {
    'description': 'Scoring Engine for Red/White/Blue Team Competitions',
    'author': 'Brandon Myers, Rusty Bower, Zack Allen',
    'url': 'https://github.com/pwnbus/scoring_engine',
    'download_url': 'https://github.com/pwnbus/scoring_engine/archive/master.zip',
    'author_email': 'pwnbus@mozilla.com, rusty@rustybower.com, zallen@fastly.com',
    'version': version,
    'install_requires': [
        'bcrypt==3.1.3',
        'celery==4.0.2',
        'configparser==3.5.0',
        'Flask==0.12',
        'Flask-Caching==1.3.3',
        'Flask-Login==0.4.0',
        'Flask-SQLAlchemy==2.2',
        'Flask-WTF==0.14.2',
        'mysqlclient==1.3.12',
        'redis==2.10.5',
        'shellescape==3.4.1',
        'pynsive==0.2.7'
    ],
    'packages': ['scoring_engine', 'bin'],
    'scripts': [],
    'name': 'scoring_engine'
}

setup(**config)
