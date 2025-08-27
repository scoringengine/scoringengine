import os

from scoring_engine.config_loader import ConfigLoader


class TestConfigLoader(object):
    def setup_method(self):
        self.config = ConfigLoader(location="../tests/scoring_engine/engine.conf.inc")

    def test_debug(self):
        assert self.config.debug is False

    def test_checks_location(self):
        assert self.config.checks_location == "scoring_engine/checks"

    def test_target_round_time(self):
        assert self.config.target_round_time == 180

    def test_agent_psk(self):
        assert self.config.agent_psk == "TheCakeIsALie"

    def test_agent_show_flag_early_mins(self):
        assert self.config.agent_show_flag_early_mins == 5

    def test_worker_refresh_time(self):
        assert self.config.worker_refresh_time == 30

    def test_blue_team_update_hostname(self):
        assert self.config.blue_team_update_hostname is True

    def test_blue_team_update_port(self):
        assert self.config.blue_team_update_port is True

    def test_blue_team_update_account_usernames(self):
        assert self.config.blue_team_update_account_usernames is True

    def test_blue_team_update_account_passwords(self):
        assert self.config.blue_team_update_account_passwords is True

    def test_blue_team_view_check_output(self):
        assert self.config.blue_team_view_check_output is True

    def test_db_uri(self):
        assert self.config.db_uri == "sqlite:////tmp/test_engine.db?check_same_thread=False"

    def test_timezone(self):
        assert self.config.timezone == "US/Eastern"

    def test_redis_host(self):
        assert self.config.redis_host == "127.0.0.1"

    def test_redis_port(self):
        assert self.config.redis_port == 6379

    def test_redis_password(self):
        assert self.config.redis_password == "testpass"

    def test_parse_sources_default(self):
        assert self.config.parse_sources("testname", "abcdefg") == "abcdefg"

    def test_parse_sources_int(self):
        assert self.config.parse_sources("testname", 1234, "int") == 1234

    def test_parse_sources_bool(self):
        assert self.config.parse_sources("testname", False, "bool") is False

    def test_worker_num_concurrent_tasks(self):
        assert self.config.worker_num_concurrent_tasks == 4

    def test_worker_queue(self):
        assert self.config.worker_queue == "main"

    def test_parse_sources_int_environment(self):
        os.environ["SCORINGENGINE_ROUND_SLEEP_TIME"] = "1"
        assert self.config.parse_sources("round_sleep_time", "1234", "int") == 1

    def test_parse_sources_bool_environment(self):
        os.environ["SCORINGENGINE_DEBUG"] = "False"
        assert self.config.parse_sources("debug", True, "bool") is False

    def test_parse_sources_str_environment(self):
        os.environ["SCORINGENGINE_REDIS_HOST"] = "127.0.0.1"
        assert self.config.parse_sources("redis_host", "1.2.3.4") == "127.0.0.1"


def test_default_uses_example_config():
    """Ensure ConfigLoader falls back to the bundled example config.

    In environments where ``engine.conf`` is not present (like CI), the
    loader should automatically read ``engine.conf.inc`` so that sensible
    defaults are available and tests can execute.
    """
    cfg = ConfigLoader()  # no explicit path provided
    # A value from engine.conf.inc confirms the fallback worked
    assert cfg.db_uri == "sqlite:////tmp/engine.db?check_same_thread=False"
