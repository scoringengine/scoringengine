import pickle
import redis

from flask import jsonify

from scoring_engine.config import config
from scoring_engine.models.team import Team

from . import mod


@mod.route('/api/scoreboard/get_bar_data')
def scoreboard_get_bar_data():
    r = redis.StrictRedis(host=config.redis_host, port=config.redis_port, db=0)
    data = r.get('get_bar_data')
    if data:
        return jsonify(pickle.loads(data))
    else:
        # TODO add updating, but in a way that does murder the database
        return jsonify({})


@mod.route('/api/scoreboard/get_line_data')
def scoreboard_get_line_data():
    results = Team.get_all_rounds_results()
    team_data = {'team': {}, 'round': results['rounds']}
    # We start at one because that's how javascript expects the team_data
    current_index = 1
    for name in results['scores'].keys():
        scores = results['scores'][name]
        rgb_color = results['rgb_colors'][name]
        team_data['team'][current_index] = {
            "label": name,
            "data": scores,
            "color": rgb_color
        }
        current_index += 1
    return jsonify(team_data)
