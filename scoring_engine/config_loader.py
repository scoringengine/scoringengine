import configparser
import os


class ConfigLoader(object):

    def __init__(self, location="../engine.conf"):
        config_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), location)

        self.parser = configparser.ConfigParser()
        self.parser.read(config_location)

        self.web_debug = self.parser['WEB']['debug'].lower() == 'true'
        self.web_caching = self.parser['WEB']['caching'].lower() == 'true'

        self.checks_location = self.parser['GENERAL']['checks_location']

        self.round_time_sleep = int(self.parser['GENERAL']['round_time_sleep'])
        self.worker_refresh_time = int(self.parser['GENERAL']['worker_refresh_time'])

        self.timezone = self.parser['GENERAL']['timezone']

        self.db_uri = self.parser['DB']['uri']

        self.redis_host = self.parser['REDIS']['host']
        self.redis_port = int(self.parser['REDIS']['port'])
        self.redis_password = self.parser['REDIS']['password']
