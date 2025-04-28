import configparser
import os


class ConfigLoader(object):
    def __init__(self, location="../engine.conf"):
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
        environment_key = "SCORINGENGINE_{}".format(key_name.upper())
        if environment_key in os.environ:
            if obj_type.lower() == "int":
                return int(os.environ[environment_key])
            elif obj_type.lower() == "bool":
                return os.environ[environment_key].lower() == "true"
            else:
                return os.environ[environment_key]
        else:
            return default_value
