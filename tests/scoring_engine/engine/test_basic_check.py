import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.basic_check import BasicCheck


class TestBasicCheck(object):

    def test_init(self):
        check = BasicCheck("127.0.0.1")
        assert check.host_address == "127.0.0.1"
