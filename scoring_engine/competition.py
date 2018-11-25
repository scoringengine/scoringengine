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
                # Verify user username
                assert 'username' in user, "'{0}' user must have a 'username' field".format(team['name'])
                assert type(user['username']) is str, "'{0}' user username must a string".format(team['name'])

                # Verify user password
                assert 'password' in user, "Team1 user must have a 'password' field"
                assert type(user['password']) is str, "'{0}' user password must a string".format(team['name'])
