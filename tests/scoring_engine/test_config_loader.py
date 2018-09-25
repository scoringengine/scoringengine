from scoring_engine.config_loader import ConfigLoader


class TestConfigLoader(object):

    def setup(self):
        self.config = ConfigLoader(location="../tests/scoring_engine/engine.conf.inc")

    def test_web_debug(self):
        assert self.config.web_debug is False

    def test_checks_location(self):
        assert self.config.checks_location == "scoring_engine/checks"

    def test_round_time_sleep(self):
        assert self.config.round_time_sleep == 180

    def test_worker_refresh_time(self):
        assert self.config.worker_refresh_time == 30

    def test_db_uri(self):
        assert self.config.db_uri == "sqlite:////tmp/test_engine.db"

    def test_timezone(self):
        assert self.config.timezone == 'US/Eastern'

    def test_redis_host(self):
        assert self.config.redis_host == "127.0.0.1"

    def test_redis_port(self):
        assert self.config.redis_port == 6379

    def test_redis_password(self):
        assert self.config.redis_password == "testpass"
