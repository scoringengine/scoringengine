try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import scoring_engine

config = {
    'description': 'Scoring Engine for Red/White/Blue Team Competitions',
    'author': 'Brandon Myers, Rusty Bower, Zack Allen',
    'url': 'https://github.com/pwnbus/scoring_engine',
    'download_url': 'https://github.com/pwnbus/scoring_engine/archive/master.zip',
    'author_email': 'pwnbus@mozilla.com, rusty@rustybower.com, zallen@fastly.com',
    'version': scoring_engine.__version__,
    'install_requires': [
        # Required Dependencies
        'bcrypt',
        'configparser',
        'Flask',
        'Flask-Cache',
        'Flask-Login',
        'Flask-SQLAlchemy',
        'Flask-WTF',
        'redis',
        'sqlalchemy',
        # Develpment Dependencies
        'pycodestyle',
        'pytest-cov',
        'pytest',
        'codeclimate-test-reporter',
        'mock'
    ],
    'packages': ['scoring_engine', 'tests', 'bin'],
    'scripts': [],
    'name': 'scoring_engine'
}

setup(**config)
