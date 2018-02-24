from scoring_engine.cache import cache


def clear_all_cache():
    from scoring_engine.web.views.api.overview import overview_get_round_data, overview_data, overview_get_columns, overview_get_data
    cache.delete_memoized(overview_get_round_data)
    cache.delete_memoized(overview_data)
    cache.delete_memoized(overview_get_columns)
    cache.delete_memoized(overview_get_data)

    from scoring_engine.web.views.api.scoreboard import scoreboard_get_bar_data, scoreboard_get_line_data
    cache.delete_memoized(scoreboard_get_bar_data)
    cache.delete_memoized(scoreboard_get_line_data)

    from scoring_engine.web.views.api.service import service_get_checks
    cache.delete_memoized(service_get_checks)

    from scoring_engine.web.views.api.team import services_get_team_data, api_services, team_services_status
    cache.delete_memoized(services_get_team_data)
    cache.delete_memoized(api_services)
    cache.delete_memoized(team_services_status)
