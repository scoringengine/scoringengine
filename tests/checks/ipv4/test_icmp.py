import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.engine import Engine


class TestICMPCheck(object):

    def test_ssh_check(self):
        engine = Engine()
        ssh_check_obj = engine.checks[0]('127.0.0.1')
        assert ssh_check_obj.command() == 'ping -c 1 127.0.0.1'
