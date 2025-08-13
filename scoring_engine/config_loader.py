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
        self.parser.read(config_location)

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
            elif obj_type.lower() == "bool":
                return env_val.lower() in ("true", "1", "yes")
            else:
                return env_val
        else:
            return default_value
