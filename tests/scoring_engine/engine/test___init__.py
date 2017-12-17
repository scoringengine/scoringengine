import sys
if 'scoring_engine.engine' in sys.modules:
    del sys.modules['scoring_engine.engine']
from scoring_engine import engine


def test_scoring_engine_engine():
    assert sys.modules['scoring_engine.engine'] == engine
