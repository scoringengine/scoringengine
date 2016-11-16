import configparser
import os


class Config(object):

    def __init__(self, location=None):
        if location is None:
            location = "../../engine.conf"
        config_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), location)

        print("Loading config from " + config_location)
        self.parser = configparser.ConfigParser()
        self.parser.read(config_location)

        self.checks_location = self.parser['GENERAL']['checks_location']
        self.check_timeout = int(self.parser['GENERAL']['check_timeout'])

        self.db_host = self.parser['DB']['host']
        self.db_port = int(self.parser['DB']['port'])
        self.db_username = self.parser['DB']['username']
        self.db_password = self.parser['DB']['password']

        self.redis_host = self.parser['REDIS']['host']
        self.redis_port = int(self.parser['REDIS']['port'])
        self.redis_password = self.parser['REDIS']['password']
        self.redis_namespace = self.parser['REDIS']['namespace']
        self.redis_queue_name = self.parser['REDIS']['queue_name']
