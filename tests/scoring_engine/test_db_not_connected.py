from scoring_engine.db_not_connected import DBNotConnected


class TestDBNotConnected(object):

    def test_init(self):
        exception = DBNotConnected()
        assert str(exception) == "DB is not connected. Must connect first"
