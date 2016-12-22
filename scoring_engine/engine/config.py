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
        self.checks_class_list = self.parser['GENERAL']['checks'].split(',')

        self.db_uri = self.parser['DB']['uri']

        self.redis_host = self.parser['REDIS']['host']
        self.redis_port = int(self.parser['REDIS']['port'])
        self.redis_password = self.parser['REDIS']['password']
        self.redis_namespace = self.parser['REDIS']['namespace']

        self.sponsorship_images = []
        for sponsorship_level in self.parser['sponsorships']['levels'].split(','):
            images = []
            for company in self.parser['sponsorships'][sponsorship_level].split(','):
                images.append("/static/" + str(company))
            self.sponsorship_images.append({"sponsorship_level": sponsorship_level, "images": images})



config = Config()
