import textwrap
from pathlib import Path

from scoring_engine.config_loader import ConfigLoader


def create_config_file(path):
    content = textwrap.dedent("""
    [OPTIONS]
    checks_location = scoring_engine/checks
    target_round_time = 180
    agent_psk = TheCakeIsALie
    agent_show_flag_early_mins = 5
    worker_refresh_time = 30
    engine_paused = False
    pause_duration = 30
    blue_team_update_hostname = True
    blue_team_update_port = True
    blue_team_update_account_usernames = True
    blue_team_update_account_passwords = True
    blue_team_view_check_output = True
    blue_team_view_status_page = True
    timezone = UTC
    upload_folder = /tmp
    debug = False
    db_uri = sqlite://
    worker_num_concurrent_tasks = -1
    worker_queue = main
    cache_type = null
    redis_host = localhost
    redis_port = 6379
    redis_password =
    """)
    with open(path, 'w') as f:
        f.write(content)


def test_boolean_env_values_recognized(tmp_path, monkeypatch):
    cfg_path = tmp_path / 'engine.conf'
    create_config_file(str(cfg_path))
    monkeypatch.setenv('SCORINGENGINE_DEBUG', '1')
    monkeypatch.setenv('SCORINGENGINE_ENGINE_PAUSED', '0')
    loader = ConfigLoader(location=str(cfg_path))
    assert loader.debug is True
    assert loader.engine_paused is False


def test_missing_option_falls_back_to_example(tmp_path):
    """Options missing from engine.conf should be populated by engine.conf.inc."""

    base_config = Path('tests/scoring_engine/engine.conf.inc').read_text()

    cfg_path = tmp_path / 'engine.conf'
    # Remove the agent_psk entry to simulate an incomplete configuration file.
    cfg_path.write_text(base_config.replace('agent_psk = TheCakeIsALie\n', ''))

    fallback_path = tmp_path / 'engine.conf.inc'
    fallback_path.write_text(base_config)

    loader = ConfigLoader(location=str(cfg_path))

    # The loader should fill the missing option from the fallback file rather
    # than raising ``KeyError``.
    assert loader.agent_psk == 'TheCakeIsALie'
