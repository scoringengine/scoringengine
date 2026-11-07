import os
import random
import shlex

CHECKS_BIN_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../checks/bin"))

CHECK_SUCCESS_TEXT = "Check Finished Successfully"
CHECK_FAILURE_TEXT = "Check Received Incorrect Content"
CHECK_TIMED_OUT_TEXT = "Check Timed Out"

SECRET_ENV_PREFIX = "SE_SECRET_"


class Secret(object):
    """A credential to pass to the check process via an environment variable.

    Returned by ``BasicCheck.secret()`` from ``command_format``. The command
    string only ever contains a reference like ``"${SE_SECRET_0}"``, so the
    plaintext value stays out of the stored ``Check.command``, the API, the
    admin dry-run and the worker logs. The worker passes the real value in the
    subprocess environment and the shell expands it at run time.
    """

    def __init__(self, value):
        self.value = "" if value is None else str(value)

    def __repr__(self):
        return "Secret(****)"


class BasicCheck(object):
    def __init__(self, environment):
        self.environment = environment
        if not hasattr(self, "required_properties"):
            self.required_properties = []
        self.set_properties()
        self.host = self.environment.service.host
        self.port = self.environment.service.port
        # Populated by command(): {env var name: secret value}
        self.command_env = {}

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

    def quote_arg(self, arg):
        return shlex.quote(arg)

    def secret(self, value):
        return Secret(value)

    def command(self):
        """Render CMD. Secrets become env var references; see command_env()."""
        args = self.command_format(self.properties)
        self.command_env = {}
        sanitized_args = []
        for arg in args:
            if isinstance(arg, Secret):
                name = SECRET_ENV_PREFIX + str(len(self.command_env))
                self.command_env[name] = arg.value
                # Double quotes so the shell expands it without word splitting
                sanitized_args.append('"${' + name + '}"')
            elif type(arg) is str:
                sanitized_args.append(self.quote_arg(arg))
            else:
                sanitized_args.append(arg)
        cmd = self.CMD.format(*sanitized_args)
        return cmd

    def get_random_account(self):
        return random.choice(self.environment.service.accounts)
