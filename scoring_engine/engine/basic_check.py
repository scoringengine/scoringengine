import random


class BasicCheck(object):
    def __init__(self, environment):
        self.environment = environment
        if not hasattr(self, 'required_properties'):
            self.required_properties = []
        self.set_properties()

    def get_ip_address(self):
        return self.environment.service.ip_address

    def get_environment_property_by_name(self, property_name):
        return [prop.value for prop in self.environment.properties if prop.name == property_name][0]

    def set_properties(self):
        self.properties = {}
        if len(self.environment.properties) != len(self.required_properties):
            raise LookupError('Not correct amount of properties for ' + self.__class__.__name__ + ' defined. Requires: ' + str(self.required_properties))

        for required_property in self.required_properties:
            self.properties[required_property] = self.get_environment_property_by_name(required_property)

    def command(self):
        args = self.command_format(self.properties)
        cmd = self.CMD.format(*args)
        return cmd

    def get_random_account(self):
        return random.choice(self.environment.service.accounts)
