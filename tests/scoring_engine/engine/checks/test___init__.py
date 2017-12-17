import sys
if 'scoring_engine.engine.checks' in sys.modules:
    del sys.modules['scoring_engine.engine.checks']
from scoring_engine.engine import checks


def test_scoring_engine_checks():
    assert sys.modules['scoring_engine.engine.checks'] == checks
