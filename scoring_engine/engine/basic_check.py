class BasicCheck(object):
    def __init__(self, service):
        self.service = service

    def environments(self):
        return self.service.environments

    def get_ip_address(self):
        return self.service.ip_address
