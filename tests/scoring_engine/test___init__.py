import sys
del sys.modules['scoring_engine']
import scoring_engine


def test_scoring_engine():
    assert sys.modules['scoring_engine'] == scoring_engine
