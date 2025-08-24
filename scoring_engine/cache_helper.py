"""Helper functions for clearing and updating application caches."""

from flask import current_app

from scoring_engine.cache import cache


def update_all_cache(app_or_ctx=None):
    """Clear and rebuild all cached values.

    Parameters
    ----------
    app_or_ctx : Flask app or app context, optional
        If provided, the cache will be cleared within this application's
        context.  If omitted, the current application context will be used.
    """

    if app_or_ctx is None:
        app_or_ctx = current_app

    context_manager = (
        app_or_ctx.app_context() if hasattr(app_or_ctx, "app_context") else app_or_ctx
    )

    with context_manager:
        cache.clear()

    update_overview_data()
    update_scoreboard_data()
    update_team_stats()
    update_services_navbar()
    update_service_data()
    update_services_data()
    update_stats()


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
        cache.delete_memoized(services_get_team_data, str(team_id))
    else:
        cache.delete_memoized(services_get_team_data)


def update_services_navbar(team_id=None):
    from scoring_engine.web.views.api.team import team_services_status

    if team_id is not None:
        cache.delete_memoized(team_services_status, str(team_id))
    else:
        cache.delete_memoized(team_services_status)


def update_service_data(service_id=None):
    from scoring_engine.web.views.api.service import service_get_checks

    if service_id is not None:
        cache.delete_memoized(service_get_checks, str(service_id))
    else:
        cache.delete_memoized(service_get_checks)


def update_services_data(team_id=None):
    from scoring_engine.web.views.api.team import api_services

    if team_id is not None:
        cache.delete_memoized(api_services, str(team_id))
    else:
        cache.delete_memoized(api_services)


# TODO - Break this into an API cache expiration
def update_stats():
    from scoring_engine.web.views.stats import home

    cache.delete_memoized(home)
