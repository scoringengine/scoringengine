from scoring_engine.cache import cache


def update_all_cache():
    update_overview_data()
    update_scoreboard_data()
    update_team_stats()
    update_services_navbar()
    update_service_data()
    update_services_data()


def update_overview_data():
    from scoring_engine.web.views.api.overview import overview_data, overview_get_data, overview_get_round_data
    cache.delete_memoized(overview_get_data)
    cache.delete_memoized(overview_data)
    cache.delete_memoized(overview_get_round_data)


def update_scoreboard_data():
    from scoring_engine.web.views.api.scoreboard import scoreboard_get_bar_data, scoreboard_get_line_data
    cache.delete_memoized(scoreboard_get_bar_data)
    cache.delete_memoized(scoreboard_get_line_data)


def update_team_stats(team_id=None):
    from scoring_engine.web.views.api.team import services_get_team_data
    if team_id is not None:
        team_id = str(team_id)
    cache.delete_memoized(services_get_team_data, team_id)


def update_services_navbar(team_id=None):
    from scoring_engine.web.views.api.team import team_services_status
    if team_id is not None:
        team_id = str(team_id)
    cache.delete_memoized(team_services_status, team_id)


def update_service_data(service_id=None):
    from scoring_engine.web.views.api.service import service_get_checks
    if service_id is not None:
        service_id = str(service_id)
    cache.delete_memoized(service_get_checks, service_id)


def update_services_data(team_id=None):
    from scoring_engine.web.views.api.team import api_services
    if team_id is not None:
        team_id = str(team_id)
    cache.delete_memoized(api_services, team_id)
