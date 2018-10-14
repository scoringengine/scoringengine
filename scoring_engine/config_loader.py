import configparser
import os


class ConfigLoader(object):

    def __init__(self, location="../engine.conf"):
        config_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), location)

        self.parser = configparser.ConfigParser()
        self.parser.read(config_location)

        self.web_debug = self.parse_sources(
            'web_debug',
            self.parser['WEB']['debug'].lower() == 'true',
            'bool'
        )

        self.checks_location = self.parse_sources(
            'checks_location',
            self.parser['GENERAL']['checks_location'],
        )

        self.round_time_sleep = self.parse_sources(
            'round_time_sleep',
            int(self.parser['GENERAL']['round_time_sleep']),
            'int'
        )

        self.worker_refresh_time = self.parse_sources(
            'worker_refresh_time',
            int(self.parser['GENERAL']['worker_refresh_time']),
            'int'
        )

        self.timezone = self.parse_sources(
            'timezone',
            self.parser['GENERAL']['timezone']
        )

        self.db_uri = self.parse_sources(
            'db_uri',
            self.parser['DB']['uri']
        )

        self.cache_type = self.parse_sources(
            'cache_type',
            self.parser['CACHE']['cache_type']
        )

        self.redis_host = self.parse_sources(
            'redis_host',
            self.parser['REDIS']['host']
        )

        self.redis_port = self.parse_sources(
            'redis_port',
            int(self.parser['REDIS']['port']),
            'int'
        )

        self.redis_password = self.parse_sources(
            'redis_password',
            self.parser['REDIS']['password']
        )

    def parse_sources(self, key_name, default_value, obj_type='str'):
        environment_key = "SCORINGENGINE_{}".format(key_name.upper())
        if environment_key in os.environ:
            if obj_type.lower() == 'int':
                return int(os.environ[environment_key])
            elif obj_type.lower() == 'bool':
                return bool(os.environ[environment_key])
            else:
                return os.environ[environment_key]
        else:
            return default_value
