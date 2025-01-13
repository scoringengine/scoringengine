import os
import random
import shlex

CHECKS_BIN_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../checks/bin"))

CHECK_SUCCESS_TEXT = "Check Finished Successfully"
CHECK_FAILURE_TEXT = "Check Received Incorrect Content"
CHECK_TIMED_OUT_TEXT = "Check Timed Out"


class BasicCheck(object):
    def __init__(self, environment):
        self.environment = environment
        if not hasattr(self, "required_properties"):
            self.required_properties = []
        self.set_properties()
        self.host = self.environment.service.host
        self.port = self.environment.service.port

    def get_environment_property_by_name(self, property_name):
        return [prop.value for prop in self.environment.properties if prop.name == property_name][0]

    def set_properties(self):
        self.properties = {}
        if len(self.environment.properties) != len(self.required_properties):
            raise LookupError(
                "Not correct amount of properties for "
                + self.__class__.__name__
                + " defined. Requires: "
                + str(self.required_properties)
            )

        for required_property in self.required_properties:
            self.properties[required_property] = self.get_environment_property_by_name(required_property)

    def command(self):
        args = self.command_format(self.properties)
        sanitized_args = []
        for arg in args:
            if type(arg) is str:
                sanitized_args.append(shlex.quote(arg))
            else:
                sanitized_args.append(arg)
        cmd = self.CMD.format(*sanitized_args)
        return cmd

    def get_random_account(self):
        return random.choice(self.environment.service.accounts)
