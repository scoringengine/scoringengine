import sys
if 'scoring_engine.engine.checks' in sys.modules:
    del sys.modules['scoring_engine.engine.checks']
import scoring_engine.engine.checks


def test_scoring_engine_checks():
    assert sys.modules['scoring_engine.engine.checks'] == scoring_engine.engine.checks
