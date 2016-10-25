import configparser
import os

class Config(object):

    def __init__(self):
        config_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../engine.conf')
        print("Loading config from " + config_location)
        self.parser = configparser.ConfigParser()
        self.parser.read(config_location)
        self.checks_location = self.parser['GENERAL']['checks_location']
