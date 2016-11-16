try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Scoring Engine for Red/White/Blue Team Competitions',
    'author': ['Brandon Myers', 'Rusty Bower'],
    'url': 'https://github.com/pwnbus/scoring_engine',
    'download_url': 'https://github.com/pwnbus/scoring_engine/archive/master.zip',
    'author_email': ['pwnbus@mozilla.com', 'rusty@rustybower.com'],
    'version': '0.0.1',
    'install_requires': ['bcrypt',
                         'codeclimate-test-reporter',
                         'configparser',
                         'Flask',
                         'Flask-Login',
                         'Flask-SQLAlchemy',
                         'Flask-WTF',
                         'pynsive',
                         'pytest',
                         'pytest-cov',
                         'redis',
                         'sqlalchemy',
                         'pycodestyle',
                         ],  # dependencies
    'packages': ['scoring_engine'],
    'scripts': [],
    'name': 'scoring_engine'
}

setup(**config)
