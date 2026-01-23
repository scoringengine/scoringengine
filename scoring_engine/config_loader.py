"""Helpers for loading configuration from files and the environment.

This module reads an ``engine.conf`` style configuration file and allows
settings to be overridden via environment variables. Each option is loaded
from the file unless a corresponding ``SCORINGENGINE_<OPTION>`` variable is
present in the environment, in which case the environment value wins.
"""

import configparser
import os


class ConfigLoader(object):
    """Load configuration values from a file with optional environment overrides."""

    def __init__(self, location="../engine.conf"):
        """Initialize the loader and parse the configuration file.

        Parameters
        ----------
        location : str, optional
            Path to the configuration file relative to this module. Defaults to
            ``"../engine.conf"``.
        """
        config_location = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), location
        )

        self.parser = configparser.ConfigParser()
        # Attempt to read the supplied configuration file.  In the test
        # environment the real ``engine.conf`` is not present and only the
        # example ``engine.conf.inc`` file exists.  Previously this resulted
        # in an empty parser which later raised ``KeyError`` when accessing
        # the ``OPTIONS`` section.  To make the loader resilient (and allow
        # tests to run in CI without a separate configuration step) we read
        # ``<location>.inc`` *before* the primary file when it is available.
        # This allows the bundled example configuration to provide defaults
        # while still letting an ``engine.conf`` override specific values.
        files_to_read = []
        if not location.endswith(".inc"):
            fallback = f"{config_location}.inc"
            if os.path.exists(fallback):
                files_to_read.append(fallback)
        files_to_read.append(config_location)
        self.parser.read(files_to_read)

        # If we still don't have an OPTIONS section, create an empty one so
        # attribute accesses below raise more informative errors during
        # testing rather than a ``KeyError`` at lookup time.
        if not self.parser.has_section("OPTIONS"):
            self.parser.add_section("OPTIONS")

        self.debug = self.parse_sources(
            "debug", self.parser["OPTIONS"]["debug"].lower() == "true", "bool"
        )

        self.checks_location = self.parse_sources(
            "checks_location",
            self.parser["OPTIONS"]["checks_location"],
        )

        self.target_round_time = self.parse_sources(
            "target_round_time", int(self.parser["OPTIONS"]["target_round_time"]), "int"
        )

        self.agent_psk = self.parse_sources(
            "agent_psk",
            self.parser["OPTIONS"]["agent_psk"],
        )

        self.agent_show_flag_early_mins = self.parse_sources(
            "agent_show_flag_early_mins", int(self.parser["OPTIONS"]["agent_show_flag_early_mins"]), "int"
        )

        self.worker_refresh_time = self.parse_sources(
            "worker_refresh_time",
            int(self.parser["OPTIONS"]["worker_refresh_time"]),
            "int",
        )

        self.engine_paused = self.parse_sources(
            "engine_paused",
            self.parser["OPTIONS"]["engine_paused"].lower() == "true",
            "bool",
        )

        self.pause_duration = self.parse_sources(
            "pause_duration",
            int(self.parser["OPTIONS"]["pause_duration"]),
            "int",
        )

        self.worker_num_concurrent_tasks = self.parse_sources(
            "worker_num_concurrent_tasks",
            int(self.parser["OPTIONS"]["worker_num_concurrent_tasks"]),
            "int",
        )

        self.blue_team_update_hostname = self.parse_sources(
            "blue_team_update_hostname",
            self.parser["OPTIONS"]["blue_team_update_hostname"].lower() == "true",
            "bool",
        )

        self.blue_team_update_port = self.parse_sources(
            "blue_team_update_port",
            self.parser["OPTIONS"]["blue_team_update_port"].lower() == "true",
            "bool",
        )

        self.blue_team_update_account_usernames = self.parse_sources(
            "blue_team_update_account_usernames",
            self.parser["OPTIONS"]["blue_team_update_account_usernames"].lower() == "true",
            "bool",
        )

        self.blue_team_update_account_passwords = self.parse_sources(
            "blue_team_update_account_passwords",
            self.parser["OPTIONS"]["blue_team_update_account_passwords"].lower() == "true",
            "bool",
        )

        self.blue_team_view_check_output = self.parse_sources(
            "blue_team_view_check_output",
            self.parser["OPTIONS"]["blue_team_view_check_output"].lower() == "true",
            "bool",
        )

        self.blue_team_view_status_page = self.parse_sources(
            "blue_team_view_status_page",
            self.parser["OPTIONS"]["blue_team_view_status_page"].lower() == "true",
            "bool",
        )

        self.worker_queue = self.parse_sources(
            "worker_queue",
            self.parser["OPTIONS"]["worker_queue"],
        )

        self.timezone = self.parse_sources(
            "timezone", self.parser["OPTIONS"]["timezone"]
        )

        self.upload_folder = self.parse_sources(
            "upload_folder", self.parser["OPTIONS"]["upload_folder"]
        )

        self.db_uri = self.parse_sources("db_uri", self.parser["OPTIONS"]["db_uri"])

        self.cache_type = self.parse_sources(
            "cache_type", self.parser["OPTIONS"]["cache_type"]
        )

        self.redis_host = self.parse_sources(
            "redis_host", self.parser["OPTIONS"]["redis_host"]
        )

        self.redis_port = self.parse_sources(
            "redis_port", int(self.parser["OPTIONS"]["redis_port"]), "int"
        )

        self.redis_password = self.parse_sources(
            "redis_password", self.parser["OPTIONS"]["redis_password"]
        )

        # SLA Penalty Configuration
        self.sla_enabled = self.parse_sources(
            "sla_enabled",
            self.parser["OPTIONS"].get("sla_enabled", "false").lower() == "true",
            "bool",
        )

        self.sla_penalty_threshold = self.parse_sources(
            "sla_penalty_threshold",
            int(self.parser["OPTIONS"].get("sla_penalty_threshold", "5")),
            "int",
        )

        self.sla_penalty_percent = self.parse_sources(
            "sla_penalty_percent",
            int(self.parser["OPTIONS"].get("sla_penalty_percent", "10")),
            "int",
        )

        self.sla_penalty_max_percent = self.parse_sources(
            "sla_penalty_max_percent",
            int(self.parser["OPTIONS"].get("sla_penalty_max_percent", "50")),
            "int",
        )

        self.sla_penalty_mode = self.parse_sources(
            "sla_penalty_mode",
            self.parser["OPTIONS"].get("sla_penalty_mode", "additive"),
        )

        self.sla_allow_negative = self.parse_sources(
            "sla_allow_negative",
            self.parser["OPTIONS"].get("sla_allow_negative", "false").lower() == "true",
            "bool",
        )

        # Dynamic Scoring Configuration
        self.dynamic_scoring_enabled = self.parse_sources(
            "dynamic_scoring_enabled",
            self.parser["OPTIONS"].get("dynamic_scoring_enabled", "false").lower() == "true",
            "bool",
        )

        self.dynamic_scoring_early_rounds = self.parse_sources(
            "dynamic_scoring_early_rounds",
            int(self.parser["OPTIONS"].get("dynamic_scoring_early_rounds", "10")),
            "int",
        )

        self.dynamic_scoring_early_multiplier = self.parse_sources(
            "dynamic_scoring_early_multiplier",
            float(self.parser["OPTIONS"].get("dynamic_scoring_early_multiplier", "2.0")),
            "float",
        )

        self.dynamic_scoring_late_start_round = self.parse_sources(
            "dynamic_scoring_late_start_round",
            int(self.parser["OPTIONS"].get("dynamic_scoring_late_start_round", "50")),
            "int",
        )

        self.dynamic_scoring_late_multiplier = self.parse_sources(
            "dynamic_scoring_late_multiplier",
            float(self.parser["OPTIONS"].get("dynamic_scoring_late_multiplier", "0.5")),
            "float",
        )

    def parse_sources(self, key_name, default_value, obj_type="str"):
        """Return a configuration value using environment overrides when present.

        Parameters
        ----------
        key_name : str
            The name of the option as defined in the configuration file.
        default_value : Any
            The value parsed from the configuration file. The return type of this
            method will match the type of ``default_value``.
        obj_type : str, optional
            Expected type of the value. Supported values are ``"str"``, ``"int"``
            and ``"bool"``. Defaults to ``"str"``.

        Returns
        -------
        Any
            Either the value from ``default_value`` or the value from the
            environment variable ``SCORINGENGINE_<KEY_NAME>`` converted to the
            requested type.
        """
        environment_key = "SCORINGENGINE_{}".format(key_name.upper())
        if environment_key in os.environ:
            env_val = os.environ[environment_key]
            if obj_type.lower() == "int":
                return int(env_val)
            elif obj_type.lower() == "float":
                return float(env_val)
            elif obj_type.lower() == "bool":
                return env_val.lower() in ("true", "1", "yes")
            else:
                return env_val
        else:
            return default_value
