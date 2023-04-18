import yaml
import datetime

from dateutil.parser import parse

from scoring_engine.config import config
from scoring_engine.engine.engine import Engine

from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.service import Service
from scoring_engine.models.account import Account
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.flag import Flag, Platform

from scoring_engine.logger import logger


class Competition(dict):
    @staticmethod
    def parse_yaml_str(input_str):
        data = yaml.safe_load(input_str)
        return Competition(data)

    def __init__(self, data):
        self.available_checks = Engine.load_check_files(config.checks_location)
        self.required_services = None
        self.verify_data(data)
        super(Competition, self).__init__(data)

    def verify_data(self, data):
        # verify teams is in project root
        assert 'teams' in data, 'teams must be defined on the root'
        assert type(data['teams']) == list, 'teams must be an array'

        for team in data['teams']:
            self.verify_team_data(team)

        # Verify there are no duplicate user usernames on any of the teams
        usernames = []
        for team in data['teams']:
            for user in team['users']:
                assert user['username'] not in usernames, "Multiple Users with the same username: '{0}'".format(user['username'])
                usernames.append(user['username'])

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

        # Verify team services if blue team
        if team['color'] == 'Blue':
            assert 'services' in team, "'{0}' must have a 'services' field".format(team['name'])
            assert type(team['services']) is list, "'{0}' 'services' field must be an array".format(team['name'])
            for service in team['services']:
                self.verify_service_data(service, team['name'])

            if self.required_services is None:
                self.required_services = []
                for service in team['services']:
                    self.required_services = team['services']

            # Verify each required service is defined on this current team
            for required_service in self.required_services:
                # Find team_service by name
                team_service = None
                for tmp_service in team['services']:
                    if tmp_service['name'] == required_service['name']:
                        team_service = tmp_service

                assert team_service is not None, "Service '{0}' not defined in team '{1}'".format(required_service['name'], team['name'])
                assert team_service['name'] == required_service['name'], "Team '{0}' missing '{1}' Expecting '{2}'".format(team['name'], required_service['name'], team_service['name'])
                assert team_service['check_name'] == required_service['check_name'], "Incorrect check_name for Service '{0}' for Team '{1}'. Got: '{2}' Expected: {3}".format(team_service['name'], team['name'], team_service['check_name'], required_service['check_name'])
                assert team_service['points'] == required_service['points'], "Incorrect points for Service '{0}' for Team '{1}'. Got: {2} Expected: {3}".format(team_service['name'], team['name'], team_service['points'], required_service['points'])
                assert len(team_service['environments']) == len(required_service['environments'])

            # Verify there aren't services defined in the current team but not in others
            for team_service in team['services']:
                required_service = None
                for tmp_service in self.required_services:
                    if tmp_service['name'] == team_service['name']:
                        required_service = tmp_service
                assert required_service is not None, "Service '{0}' for Team '{1}' not defined in other teams".format(team_service['name'], team['name'])

            # Verify each team service must have unique names
            team_service_names = []
            for service in team['services']:
                assert service['name'] not in team_service_names, "Each team's service must have a unique name, found duplicates in '{0}' for team '{1}'".format(service['name'], team['name'])
                team_service_names.append(service['name'])

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

        # Verify service worker_queue if it exists
        if 'worker_queue' in service:
            assert type(service['worker_queue']) is str, "{0} {1} service 'worker_queue' field must be a string".format(team_name, service['name'])

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
        # Verify environment matching_content
        assert 'matching_content' in environment, "{0} {1} environment must have a 'matching_content' field".format(team_name, service_name)
        assert type(environment['matching_content']) is str, "{0} {1} environment 'matching_content' field must be a string".format(team_name, service_name)

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

    def save(self, db_session):
        for team_dict in self['teams']:
            logger.info("Creating {0} Team: {1}".format(team_dict['color'], team_dict['name']))
            team_obj = Team(name=team_dict['name'], color=team_dict['color'])
            db_session.add(team_obj)
            for user_dict in team_dict['users']:
                logger.info("\tCreating User {0}:{1}".format(user_dict['username'], user_dict['password']))
                db_session.add(User(username=user_dict['username'], password=user_dict['password'], team=team_obj))
            if 'services' in team_dict:
                for service_dict in team_dict['services']:
                    logger.info("\tCreating {0} Service".format(service_dict['name']))
                    service_obj = Service(
                        name=service_dict['name'],
                        team=team_obj,
                        check_name=service_dict['check_name'],
                        host=service_dict['host'],
                        port=service_dict['port'],
                        points=service_dict['points']
                    )
                    if 'worker_queue' in service_dict:
                        service_obj.worker_queue = service_dict['worker_queue']
                    db_session.add(service_obj)
                    if 'accounts' in service_dict:
                        for account_dict in service_dict['accounts']:
                            db_session.add(Account(username=account_dict['username'], password=account_dict['password'], service=service_obj))
                    for environment_dict in service_dict['environments']:
                        environment_obj = Environment(service=service_obj, matching_content=environment_dict['matching_content'])
                        db_session.add(environment_obj)
                        if 'properties' in environment_dict:
                            for property_dict in environment_dict['properties']:
                                db_session.add(Property(environment=environment_obj, name=property_dict['name'], value=property_dict['value']))
            db_session.commit()
        for flag in self["flags"]:
            start = flag.get("start_time", None)
            end = flag.get("end_time", None)
            if not start:
                start = str(datetime.datetime.utcnow()) # TODO - This is hacky, find a better way to fix this
            if not end:
                end = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)) # TODO - This is hacky, find a better way to fix this
            f = Flag(
                type=flag["type"],
                platform=Platform(flag["platform"]),
                data=flag["data"],
                start_time=parse(start),
                end_time=parse(end),
                perm=flag["perm"]
            )
            db_session.add(f)
        db_session.commit()