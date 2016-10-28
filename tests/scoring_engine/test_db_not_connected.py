import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from db_not_connected import DBNotConnected


class TestDBNotConnected(object):

    def test_init(self):
        exception = DBNotConnected()
        assert str(exception) == "DB is not connected. Must connect first"
