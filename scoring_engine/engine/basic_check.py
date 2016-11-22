class BasicCheck(object):
    def __init__(self, service):
        self.service = service

    def properties(self):
        return self.service.properties

    def get_ip_address(self):
        return self.service.ip_address
