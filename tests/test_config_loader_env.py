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


def test_missing_required_option_falls_back_to_example(tmp_path):
    """Options missing from engine.conf should be populated by engine.conf.inc."""

    base_config = Path('tests/scoring_engine/engine.conf.inc').read_text()

    cfg_path = tmp_path / 'engine.conf'
    # Remove the timezone entry to simulate an incomplete configuration file.
    cfg_path.write_text(base_config.replace('timezone = US/Eastern\n', ''))

    fallback_path = tmp_path / 'engine.conf.inc'
    fallback_path.write_text(base_config)

    loader = ConfigLoader(location=str(cfg_path))

    # The loader should fill the missing option from the fallback file rather
    # than raising ``KeyError``.
    assert loader.timezone == 'US/Eastern'


def test_missing_optional_agent_module_disables_feature(tmp_path):
    base_config = Path('tests/scoring_engine/engine.conf.inc').read_text()

    cfg_path = tmp_path / 'engine.conf'
    cfg_path.write_text(base_config.replace('agent_psk = TheCakeIsALie\n', ''))

    loader = ConfigLoader(location=str(cfg_path))

    assert loader.agent_psk is None
    modules = {module['key']: module for module in loader.modules}
    agent_module = modules['black_team_agent']
    assert agent_module['configured'] is False
    assert 'agent_psk' in agent_module['missing']
