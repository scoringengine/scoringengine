"""Helpers for loading configuration from files and the environment.

This module reads an ``engine.conf`` style configuration file and allows
settings to be overridden via environment variables. Each option is loaded
from the file unless a corresponding ``SCORINGENGINE_<OPTION>`` variable is
set to a non-empty value in the environment, in which case the environment
value wins.

An environment variable that exists but is empty (or contains only whitespace)
is treated as *not set* and does not override the configuration file. This
matters because environment files are usually created by copying an example
(``cp .env.example .env``) and ``docker compose`` happily forwards a bare
``SCORINGENGINE_FOO=`` line into the container as an empty string. Without this
rule, an untouched placeholder line would silently blank out a value that was
correctly set in ``engine.conf`` -- for string options that means an empty
value, and for ``int``/``float`` options it meant a ``ValueError`` at startup.

The consequence is that an option cannot be forced to an empty value *from the
environment*; set it empty in the configuration file instead (this is how
``redis_password`` ships).
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
        config_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), location)

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

        self.debug = self.parse_sources("debug", self.parser["OPTIONS"]["debug"].lower() == "true", "bool")

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

        self.max_consecutive_round_failures = self.parse_sources(
            "max_consecutive_round_failures",
            int(self.parser["OPTIONS"].get("max_consecutive_round_failures", "3")),
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

        self.task_jitter_max_delay = self.parse_sources(
            "task_jitter_max_delay",
            int(self.parser["OPTIONS"].get("task_jitter_max_delay", "0")),
            "int",
        )

        self.anonymize_team_names = self.parse_sources(
            "anonymize_team_names",
            self.parser["OPTIONS"].get("anonymize_team_names", "false").lower() == "true",
            "bool",
        )

        self.worker_queue = self.parse_sources(
            "worker_queue",
            self.parser["OPTIONS"]["worker_queue"],
        )

        # Tool packs installed on this worker (see scoring_engine/worker_packs.py).
        # Docker images set SCORINGENGINE_WORKER_PACKS per build target.
        self.worker_packs = self.parse_sources(
            "worker_packs",
            self.parser["OPTIONS"].get("worker_packs", "core,db,rdp,browser"),
        )

        self.timezone = self.parse_sources("timezone", self.parser["OPTIONS"]["timezone"])

        self.upload_folder = self.parse_sources("upload_folder", self.parser["OPTIONS"]["upload_folder"])

        self.check_output_folder = self.parse_sources(
            "check_output_folder",
            self.parser["OPTIONS"].get("check_output_folder", "/var/check_outputs"),
        )

        # Flask session signing key used by the web application.
        #
        # There is deliberately no default value here: shipping a fixed key
        # would let anyone forge session cookies against every deployment that
        # never changed it.  An empty string means "not configured", and the
        # web app generates a random key at startup (and warns loudly).
        self.secret_key = self.parse_sources(
            "secret_key",
            self.parser["OPTIONS"].get("secret_key", ""),
        )

        self.db_uri = self.parse_sources("db_uri", self.parser["OPTIONS"]["db_uri"])

        self.cache_type = self.parse_sources("cache_type", self.parser["OPTIONS"]["cache_type"])

        self.redis_host = self.parse_sources("redis_host", self.parser["OPTIONS"]["redis_host"])

        self.redis_port = self.parse_sources("redis_port", int(self.parser["OPTIONS"]["redis_port"]), "int")

        self.redis_password = self.parse_sources("redis_password", self.parser["OPTIONS"]["redis_password"])

        # Mark the session/remember-me cookies Secure so browsers only ever send
        # them over HTTPS.  Correct for the shipped docker deployment (nginx
        # terminates TLS and 301s port 80 to 443) but it must stay off for a
        # plain-HTTP dev run, otherwise the browser drops the cookie and login
        # silently fails.  Defaults to False so an unconfigured checkout works.
        self.session_cookie_secure = self.parse_sources(
            "session_cookie_secure",
            self.parser["OPTIONS"].get("session_cookie_secure", "false").lower() == "true",
            "bool",
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

        # Inject Score Visibility
        self.inject_scores_visible = self.parse_sources(
            "inject_scores_visible",
            self.parser["OPTIONS"].get("inject_scores_visible", "false").lower() == "true",
            "bool",
        )

        # Red-team flag scoring: flat points per captured flag by permission level.
        self.flag_points_user = self.parse_sources(
            "flag_points_user",
            int(self.parser["OPTIONS"].get("flag_points_user", "100")),
            "int",
        )
        self.flag_points_root = self.parse_sources(
            "flag_points_root",
            int(self.parser["OPTIONS"].get("flag_points_root", "200")),
            "int",
        )

        # Weighted scoring: rebalance how service uptime, injects, and flag
        # captures contribute to the combined scoreboard total. Every weight is a
        # multiplier (1.0 = no change); the whole feature is off unless enabled.
        self.weighted_scoring_enabled = self.parse_sources(
            "weighted_scoring_enabled",
            self.parser["OPTIONS"].get("weighted_scoring_enabled", "false").lower() == "true",
            "bool",
        )
        self.service_weight = self.parse_sources(
            "service_weight",
            float(self.parser["OPTIONS"].get("service_weight", "1.0")),
            "float",
        )
        self.inject_weight = self.parse_sources(
            "inject_weight",
            float(self.parser["OPTIONS"].get("inject_weight", "1.0")),
            "float",
        )
        self.flag_weight = self.parse_sources(
            "flag_weight",
            float(self.parser["OPTIONS"].get("flag_weight", "1.0")),
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
            Expected type of the value. Supported values are ``"str"``,
            ``"int"``, ``"float"`` and ``"bool"``. Defaults to ``"str"``.

        Returns
        -------
        Any
            Either the value from ``default_value`` or the value from the
            environment variable ``SCORINGENGINE_<KEY_NAME>`` converted to the
            requested type.

        Notes
        -----
        An environment variable that is present but empty (or whitespace only)
        is deliberately treated as absent, so it does not override a value that
        was set in the configuration file. See the module docstring for why.
        """
        environment_key = "SCORINGENGINE_{}".format(key_name.upper())
        env_val = os.environ.get(environment_key)

        # An empty environment variable means "not configured", not "configure
        # this to nothing". A commented-out or untouched placeholder line in a
        # copied .env must never blank out engine.conf.
        if env_val is None or not env_val.strip():
            return default_value

        if obj_type.lower() == "int":
            return int(env_val)
        elif obj_type.lower() == "float":
            return float(env_val)
        elif obj_type.lower() == "bool":
            return env_val.strip().lower() in ("true", "1", "yes")
        else:
            return env_val
