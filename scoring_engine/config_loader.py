"""Helpers for loading configuration from files and the environment.

This module reads an ``engine.conf`` style configuration file and allows
settings to be overridden via environment variables. Each option is loaded
from the file unless a corresponding ``SCORINGENGINE_<OPTION>`` variable is
present in the environment, in which case the environment value wins.
"""

import configparser
import os
from typing import Any, Dict, List, Set

from scoring_engine.logger import logger


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

        self._user_defined_options = self._load_user_defined_options(config_location)

        # If we still don't have an OPTIONS section, create an empty one so
        # attribute accesses below raise more informative errors during
        # testing rather than a ``KeyError`` at lookup time.
        if not self.parser.has_section("OPTIONS"):
            self.parser.add_section("OPTIONS")

        self.modules: List[Dict[str, Any]] = []
        self._module_index: Dict[str, Dict[str, Any]] = {}

        self.debug = self._load_option("debug", obj_type="bool")
        self.checks_location = self._load_option("checks_location")
        self.target_round_time = self._load_option(
            "target_round_time", obj_type="int"
        )
        self.agent_psk = self._load_option(
            "agent_psk", required=False, use_fallback=False
        )
        self.agent_show_flag_early_mins = self._load_option(
            "agent_show_flag_early_mins",
            obj_type="int",
            required=False,
            use_fallback=False,
        )
        self.worker_refresh_time = self._load_option(
            "worker_refresh_time", obj_type="int"
        )
        self.engine_paused = self._load_option(
            "engine_paused", obj_type="bool"
        )
        self.pause_duration = self._load_option("pause_duration", obj_type="int")
        self.worker_num_concurrent_tasks = self._load_option(
            "worker_num_concurrent_tasks", obj_type="int"
        )
        self.blue_team_update_hostname = self._load_option(
            "blue_team_update_hostname", obj_type="bool"
        )
        self.blue_team_update_port = self._load_option(
            "blue_team_update_port", obj_type="bool"
        )
        self.blue_team_update_account_usernames = self._load_option(
            "blue_team_update_account_usernames", obj_type="bool"
        )
        self.blue_team_update_account_passwords = self._load_option(
            "blue_team_update_account_passwords", obj_type="bool"
        )
        self.blue_team_view_check_output = self._load_option(
            "blue_team_view_check_output", obj_type="bool"
        )
        self.worker_queue = self._load_option("worker_queue")
        self.timezone = self._load_option("timezone")
        self.upload_folder = self._load_option("upload_folder")
        self.db_uri = self._load_option("db_uri")
        self.cache_type = self._load_option(
            "cache_type", fallback="null", required=False
        )
        self.redis_host = self._load_option(
            "redis_host", required=False
        )
        self.redis_port = self._load_option(
            "redis_port", obj_type="int", required=False
        )
        self.redis_password = self._load_option(
            "redis_password", required=False
        )

        self._register_non_core_modules()

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
            return self._coerce(env_val, obj_type)
        else:
            return default_value

    def _load_user_defined_options(self, config_location: str) -> Set[str]:
        options: Set[str] = set()
        if os.path.exists(config_location):
            user_parser = configparser.ConfigParser()
            user_parser.read(config_location)
            if user_parser.has_section("OPTIONS"):
                options.update(user_parser["OPTIONS"].keys())
        return options

    def _coerce(self, value: Any, obj_type: str) -> Any:
        if value is None:
            return None
        if obj_type.lower() == "int":
            return int(value)
        if obj_type.lower() == "bool":
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes", "on")
        return value if isinstance(value, str) else str(value)

    def _load_option(
        self,
        key_name: str,
        obj_type: str = "str",
        required: bool = True,
        fallback: Any = None,
        use_fallback: bool = True,
    ) -> Any:
        environment_key = f"SCORINGENGINE_{key_name.upper()}"
        if environment_key in os.environ:
            return self._coerce(os.environ[environment_key], obj_type)

        if self.parser.has_option("OPTIONS", key_name):
            if use_fallback or key_name in self._user_defined_options:
                raw_value = self.parser["OPTIONS"][key_name]
                return self._coerce(raw_value, obj_type)

        if required:
            raise configparser.NoOptionError(key_name, "OPTIONS")

        if fallback is not None:
            return self._coerce(fallback, obj_type)

        return None

    def _register_non_core_modules(self) -> None:
        bta_missing: List[str] = []
        if not self.agent_psk:
            bta_missing.append("agent_psk")
        elif self.agent_show_flag_early_mins is None:
            bta_missing.append("agent_show_flag_early_mins")

        bta_enabled = bool(self.agent_psk)
        bta_configured = bta_enabled and not bta_missing
        self._register_module(
            key="black_team_agent",
            name="Black Team Agent",
            enabled=bta_enabled,
            configured=bta_configured,
            missing=bta_missing,
        )

        cache_missing: List[str] = []
        cache_enabled = bool(self.cache_type) and str(self.cache_type).lower() not in (
            "null",
            "none",
            "disabled",
        )
        if cache_enabled:
            if not self.redis_host:
                cache_missing.append("redis_host")
            if self.redis_port is None:
                cache_missing.append("redis_port")
        cache_configured = cache_enabled and not cache_missing
        self._register_module(
            key="redis_cache",
            name="Redis Cache",
            enabled=cache_enabled,
            configured=cache_configured,
            missing=cache_missing,
        )

    def _register_module(
        self,
        *,
        key: str,
        name: str,
        enabled: bool,
        configured: bool,
        missing: List[str],
    ) -> None:
        module = {
            "key": key,
            "name": name,
            "enabled": enabled,
            "configured": configured,
            "missing": missing,
        }
        self.modules.append(module)
        self._module_index[key] = module

        if not configured:
            if missing:
                logger.warning(
                    "Non-core module '%s' is disabled or misconfigured. Missing values: %s",
                    name,
                    ", ".join(missing),
                )
            else:
                logger.info("Non-core module '%s' is disabled.", name)

    def module(self, key: str) -> Dict[str, Any]:
        return self._module_index.get(key, {})
