class BasicCheck(object):
    def __init__(self, environment):
        self.environment = environment

    def get_ip_address(self):
        return self.environment.service.ip_address

    def get_property_by_name(self, property_name):
      return [prop.value for prop in self.environment.properties if prop.name == property_name][0]
