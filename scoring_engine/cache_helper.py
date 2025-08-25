"""Helper functions for clearing and updating application caches."""

from flask import current_app
from flask_caching.backends import NullCache
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
    # corresponds with file scoring_engine.web.views.api.team function services_get_team_data

    if team_id is not None:
        cache.delete(f"/api/team/{team_id}/stats_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.keys("*/api/team/*/stats_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))

def update_services_navbar(team_id=None):
    # corresponds with file scoring_engine.web.views.api.team function team_services_status

    if team_id is not None:
        cache.delete(f"/api/team/{team_id}/services/status_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.keys("*/api/team/*/services/status_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_service_data(service_id=None):
    # corresponds with file scoring_engine.web.views.api.service function service_get_checks

    if service_id is not None:
        # we don't need to know the team_id for the final part because each service id is globally unique so this will only delete one team's cache of a specific service's data
        cache.delete(f"/api/service/{service_id}/checks_*")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.keys("*/api/service/*/checks_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))

def update_services_data(team_id=None):
    # corresponds with file scoring_engine.web.views.api.team function api_services

    if team_id is not None:
        cache.delete(f"/api/team/{team_id}/services_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.keys("*/api/team/*/services_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


# TODO - Break this into an API cache expiration
def update_stats():
    from scoring_engine.web.views.stats import home

    cache.delete_memoized(home)
