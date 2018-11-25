import hjson

from scoring_engine import config
from scoring_engine.engine.engine import Engine


class Competition(dict):
    def parse_json_str(json_str):
        data = hjson.loads(json_str)
        return Competition(data)

    def __init__(self, data):
        self.available_checks = Engine.load_check_files(config.checks_location)
        self.verify_data(data)

    def verify_data(self, data):
        # verify teams is in project root
        assert 'teams' in data, 'teams must be defined on the root'
        assert type(data['teams']) == list, 'teams must be an array'

        for team in data['teams']:
            self.verify_team_data(team)

    def verify_team_data(self, team):
        # Verify team name
        assert 'name' in team, "team must have a 'name' field"
        assert type(team['name']) is str, 'team name must be a string'

        # Verify team color
        assert 'color' in team, "'{0}' must have a 'color' field".format(team['name'])
        assert type(team['color']) is str, "'{0}' color must a string".format(team['name'])
        assert team['color'] in ('Blue', 'White', 'Red'), "'{0}' color must one of (Red, White, Blue)".format(team['name'])

        # Verify team users
        assert 'users' in team, "'{0}' must have a 'users' field".format(team['name'])
        assert type(team['users']) is list, "'{0}' 'users' field must be an array".format(team['name'])
        for user in team['users']:
            self.verify_user_data(user, team['name'])

        # Verify team services
        assert 'services' in team, "'{0}' must have a 'services' field".format(team['name'])
        assert type(team['services']) is list, "'{0}' 'services' field must be an array".format(team['name'])
        for service in team['services']:
            self.verify_service_data(service, team['name'])

    def verify_user_data(self, user, team_name):
        # Verify user username
        assert 'username' in user, "{0} user must have a 'username' field".format(team_name)
        assert type(user['username']) is str, "{0} user username must a string".format(team_name)

        # Verify user password
        assert 'password' in user, "{0} user must have a 'password' field".format(team_name)
        assert type(user['password']) is str, "{0} user password must a string".format(team_name)

    def verify_service_data(self, service, team_name):
        # Verify service name
        assert 'name' in service, "{0} service must have a 'name' field".format(team_name)
        assert type(service['name']) is str, "{0} service 'name' must be a string".format(team_name)

        # Verify service check_name
        assert 'check_name' in service, "{0} {1} service must have a 'check_name' field".format(team_name, service['name'])
        assert type(service['check_name']) is str, "{0} {1} service 'check_name' field must be a string".format(team_name, service['name'])
        # Verify check_name maps correctly to a real check source code class
        found_check = None
        for available_check in self.available_checks:
            if service['check_name'] == available_check.__name__:
                found_check = available_check
        assert found_check is not None, "{0} {1} Incorrect 'check_name' field, must match the classname of a check defined in {2}".format(team_name, service['name'], config.checks_location)

        # Verify service host
        assert 'host' in service, "{0} {1} service must have a 'host' field".format(team_name, service['name'])
        assert type(service['host']) is str, "{0} {1} service 'host' field must be a string".format(team_name, service['name'])

        # Verify service port
        assert 'port' in service, "{0} {1} service must have a 'port' field".format(team_name, service['name'])
        assert type(service['port']) is int, "{0} {1} service 'port' field must be an integer".format(team_name, service['name'])

        # Verify service points
        assert 'points' in service, "{0} {1} service must have a 'points' field".format(team_name, service['name'])
        assert type(service['points']) is int, "{0} {1} service 'points' field must be an integer".format(team_name, service['name'])

        if 'accounts' in service:
            assert type(service['accounts']) is list, "{0} {1} service 'accounts' field must be an array".format(team_name, service['name'])
            for account in service['accounts']:
                self.verify_account_data(account, team_name, service['name'])

        # Verify service environments
        assert 'environments' in service, "{0} {1} service must have a 'environments' field".format(team_name, service['name'])
        assert type(service['environments']) is list, "{0} {1} service 'environments' field must be an array".format(team_name, service['name'])
        for environment in service['environments']:
            self.verify_environment_data(environment, team_name, service['name'], found_check)

    def verify_account_data(self, account, team_name, service_name):
        # Verify account username
        assert 'username' in account, "{0} {1} account must have a 'username' field".format(team_name, service_name)
        assert type(account['username']) is str, "{0} {1} account 'username' field must be a string".format(team_name, service_name)

        # Verify account password
        assert 'password' in account, "{0} {1} account must have a 'password' field".format(team_name, service_name)
        assert type(account['password']) is str, "{0} {1} account 'password' field must be a string".format(team_name, service_name)

    def verify_environment_data(self, environment, team_name, service_name, found_check_source):
        # Verify environment matching_regex
        assert 'matching_regex' in environment, "{0} {1} environment must have a 'matching_regex' field".format(team_name, service_name)
        assert type(environment['matching_regex']) is str, "{0} {1} environment 'matching_regex' field must be a string".format(team_name, service_name)

        # Verify environment properties
        if 'properties' in environment:
            assert type(environment['properties']) is list, "{0} {1} environment 'properties' field must be an array".format(team_name, service_name)
            for property_obj in environment['properties']:
                self.verify_property_data(property_obj, team_name, service_name, found_check_source)
            # Verify that all properties the check source code requires, is listed
            for required_property_key in found_check_source.required_properties:
                matched_key = False
                for defined_property in environment['properties']:
                    if required_property_key in defined_property['name']:
                        matched_key = True
                assert matched_key is True, "{0} {1} service does not define the '{2}' property".format(team_name, service_name, required_property_key)

    def verify_property_data(self, property_obj, team_name, service_name, found_check_source):
        # Verify property name
        assert 'name' in property_obj, "{0} {1} property must have a 'name' field".format(team_name, service_name)
        assert type(property_obj['name']) is str, "{0} {1} property 'name' field must be a string".format(team_name, service_name)

        # Verify property value
        assert 'value' in property_obj, "{0} {1} property must have a 'value' field".format(team_name, service_name)
        assert type(property_obj['value']) is str, "{0} {1} property 'value' field must be a string".format(team_name, service_name)
        assert property_obj['name'] in found_check_source.required_properties, "{0} {1} {2} does not require the property '{3}'".format(team_name, service_name, found_check_source.__name__, property_obj['name'])
