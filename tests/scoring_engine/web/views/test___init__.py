import sys
if 'scoring_engine.web.views' in sys.modules:
    del sys.modules['scoring_engine.web.views']
import scoring_engine.web.views


def test_scoring_engine_web():
    assert sys.modules['scoring_engine.web.views'] == scoring_engine.web.views
