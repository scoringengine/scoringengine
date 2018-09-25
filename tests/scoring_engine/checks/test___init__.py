import sys
if 'scoring_engine.checks' in sys.modules:
    del sys.modules['scoring_engine.checks']
import scoring_engine.checks


def test_scoring_engine_checks():
    assert sys.modules['scoring_engine.checks'] == scoring_engine.checks
