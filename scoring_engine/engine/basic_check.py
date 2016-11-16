class BasicCheck(object):
    def __init__(self, service):
        self.service = service

    def properties(self):
        return self.service.properties

    def get_ip_address(self):
        ip = [property_obj.value for property_obj in self.properties() if property_obj.name == 'IP Address']
        if ip:
          return ip[0]
        else:
          raise LookupError('IP Address property does not exist')
