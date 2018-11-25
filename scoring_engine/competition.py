import hjson


class Competition(dict):
    def parse_json_str(json_str):
        data = hjson.loads(json_str)
        Competition.verify_data(data)
        return Competition(data)

    def verify_data(data):
        # verify teams is in project root
        assert 'teams' in data, 'teams must be defined on the root'
        assert type(data['teams']) == list, 'teams must be an array'

        for team in data['teams']:
            Competition.verify_team_data(team)

    def verify_team_data(team):
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
            Competition.verify_user_data(user, team['name'])

        # Verify team services
        assert 'services' in team, "'{0}' must have a 'services' field".format(team['name'])
        assert type(team['services']) is list, "'{0}' 'services' field must be an array".format(team['name'])
        for service in team['services']:
            Competition.verify_service_data(service, team['name'])

    def verify_user_data(user, team_name):
        # Verify user username
        assert 'username' in user, "{0} user must have a 'username' field".format(team_name)
        assert type(user['username']) is str, "{0} user username must a string".format(team_name)

        # Verify user password
        assert 'password' in user, "{0} user must have a 'password' field".format(team_name)
        assert type(user['password']) is str, "{0} user password must a string".format(team_name)

    def verify_service_data(service, team_name):
        # Verify service name
        assert 'name' in service, "{0} service must have a 'name' field".format(team_name)
        assert type(service['name']) is str, "{0} service 'name' must be a string".format(team_name)

        # Verify service check_name
        assert 'check_name' in service, "{0} {1} service must have a 'check_name' field".format(team_name, service['name'])
        assert type(service['check_name']) is str, "{0} {1} service 'check_name' field must be a string".format(team_name, service['name'])
        # todo: verify the check_name maps correctly to real check

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
                Competition.verify_account_data(account, team_name, service['name'])

        Competition.verify_environment_data(environment, team_name, service['name'])

    def verify_account_data(account, team_name, service_name):
        # verify username field and it's a string
        # verify password field and it's a string
        pass

    def verify_environment_data(environment, team_name, service_name):
        # verify has matching_regex field and it's either a string or a regex
        # verify has properties field and it's an array
        # pass
