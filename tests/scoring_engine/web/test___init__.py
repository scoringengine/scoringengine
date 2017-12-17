import sys
if 'scoring_engine.engine' in sys.modules:
    del sys.modules['scoring_engine.web']
from scoring_engine import web


def test_scoring_engine_web():
    assert sys.modules['scoring_engine.web'] == web
