from scoring_engine.config_loader import ConfigLoader


class MockConfig(object):
    def __init__(self, location):
        self.file_location = location

    @property
    def config(self):
        return ConfigLoader(self.file_location)
