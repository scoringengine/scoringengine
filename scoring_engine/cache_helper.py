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

    context_manager = app_or_ctx.app_context() if hasattr(app_or_ctx, "app_context") else app_or_ctx

    with context_manager:
        cache.clear()

    update_overview_data()
    update_scoreboard_data()
    update_team_stats()
    update_services_navbar()
    update_service_data()
    update_services_data()
    update_announcements_data()
    update_stats()


def update_overview_data():
    from scoring_engine.web.views.api.overview import (
        overview_get_data,
        overview_get_round_data,
        _get_overview_data_cached,
        _get_table_columns_cached,
    )

    cache.delete_memoized(overview_get_data)
    cache.delete_memoized(overview_get_round_data)
    cache.delete_memoized(_get_overview_data_cached)
    cache.delete_memoized(_get_table_columns_cached)


def update_scoreboard_data():
    from scoring_engine.web.views.api.scoreboard import _get_bar_data_cached, _get_line_data_cached

    cache.delete_memoized(_get_bar_data_cached)
    cache.delete_memoized(_get_line_data_cached)


def update_team_stats(team_id=None):
    # corresponds with file scoring_engine.web.views.api.team function services_get_team_data

    if team_id is not None:
        cache.delete(f"/api/team/{team_id}/stats_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match="*/api/team/*/stats_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_services_navbar(team_id=None):
    # corresponds with file scoring_engine.web.views.api.team function team_services_status

    if team_id is not None:
        cache.delete(f"/api/team/{team_id}/services/status_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match="*/api/team/*/services/status_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_service_data(service_id=None):
    # corresponds with file scoring_engine.web.views.api.service function service_get_checks

    if service_id is not None:
        # we don't need to know the team_id for the final part because each service id is globally unique so this will only delete one team's cache of a specific service's data
        cache.delete(f"/api/service/{service_id}/checks_*")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match="*/api/service/*/checks_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_services_data(team_id=None):
    # corresponds with file scoring_engine.web.views.api.team function api_services

    if team_id is not None:
        cache.delete(f"/api/team/{team_id}/services_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match="*/api/team/*/services_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_announcements_data():
    """Clear cached announcement data for all visibility contexts."""
    if not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match="*/api/announcements_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_inject_data(inject_id, team_id=None):
    """Clear cached inject detail for the given inject.

    The cache key for ``/api/inject/<id>`` is ``/api/inject/<id>_<team_id>``.
    Both the owning team and the white team can view an inject, so we clear
    all matching keys when ``team_id`` is not provided.
    """
    if team_id is not None:
        cache.delete(f"/api/inject/{inject_id}_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match=f"*/api/inject/{inject_id}_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_inject_comments(inject_id, team_id=None):
    """Clear cached inject comments for the given inject."""
    if team_id is not None:
        cache.delete(f"/api/inject/{inject_id}/comments_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match=f"*/api/inject/{inject_id}/comments_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_inject_files(inject_id, team_id=None):
    """Clear cached inject files for the given inject."""
    if team_id is not None:
        cache.delete(f"/api/inject/{inject_id}/files_{team_id}")
    elif not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match=f"*/api/inject/{inject_id}/files_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_all_inject_data():
    """Clear all cached inject detail and inject list data for all teams."""
    if not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match="*/api/inject*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))


def update_stats():
    # Clear cached /api/stats responses (keyed per-team/role)
    if not isinstance(cache.cache, NullCache):
        for key in cache.cache._write_client.scan_iter(match="*/api/stats_*"):
            cache.delete(key.decode("utf-8").removeprefix(cache.cache.key_prefix))
