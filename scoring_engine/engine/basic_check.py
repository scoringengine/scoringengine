class BasicCheck(object):
    def __init__(self, environment):
        self.environment = environment

    def get_ip_address(self):
        return self.environment.service.ip_address
