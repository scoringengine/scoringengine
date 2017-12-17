import sys
if 'scoring_engine.engine' in sys.modules:
    del sys.modules['scoring_engine.engine']
import scoring_engine.engine


def test_scoring_engine_engine():
    assert sys.modules['scoring_engine.engine'] == scoring_engine.engine
