"""Cache invalidation helpers for the scoring engine's web interface.

These utilities clear memoized responses for various API endpoints so that
updated scoring data is served after state changes occur.
"""

from scoring_engine.cache import cache
from scoring_engine.web import create_app


def update_all_cache():
    """Clear all cached data and regenerate cached sections."""

    app = create_app()
    with app.app_context():
        cache.clear()

    update_overview_data()
    update_scoreboard_data()
    update_team_stats()
    update_services_navbar()
    update_service_data()
    update_services_data()
    update_stats()


def update_overview_data():
    """Invalidate cached overview API responses."""

    from scoring_engine.web.views.api.overview import overview_data, overview_get_data, overview_get_round_data

    cache.delete_memoized(overview_get_data)
    cache.delete_memoized(overview_data)
    cache.delete_memoized(overview_get_round_data)


def update_scoreboard_data():
    """Invalidate cached scoreboard API responses."""

    from scoring_engine.web.views.api.scoreboard import scoreboard_get_bar_data, scoreboard_get_line_data

    cache.delete_memoized(scoreboard_get_bar_data)
    cache.delete_memoized(scoreboard_get_line_data)


def update_team_stats(team_id=None):
    """Invalidate cached team statistics.

    Args:
        team_id: Optional team identifier to target a specific team. If
            ``None`` (default), clears stats for all teams.
    """

    from scoring_engine.web.views.api.team import services_get_team_data

    if team_id is not None:
        cache.delete_memoized(services_get_team_data, str(team_id))
    else:
        cache.delete_memoized(services_get_team_data)


def update_services_navbar(team_id=None):
    """Invalidate cached service status navbar data.

    Args:
        team_id: Optional team identifier to refresh a single team's navbar.
            If ``None``, all teams are refreshed.
    """

    from scoring_engine.web.views.api.team import team_services_status

    if team_id is not None:
        cache.delete_memoized(team_services_status, str(team_id))
    else:
        cache.delete_memoized(team_services_status)


def update_service_data(service_id=None):
    """Invalidate cached checks for a service.

    Args:
        service_id: Optional service identifier to refresh a single service.
            If ``None``, all services are refreshed.
    """

    from scoring_engine.web.views.api.service import service_get_checks

    if service_id is not None:
        cache.delete_memoized(service_get_checks, str(service_id))
    else:
        cache.delete_memoized(service_get_checks)


def update_services_data(team_id=None):
    """Invalidate cached service listings for a team.

    Args:
        team_id: Optional team identifier whose services should be
            invalidated. If ``None``, caches for all teams are cleared.
    """

    from scoring_engine.web.views.api.team import api_services

    if team_id is not None:
        cache.delete_memoized(api_services, str(team_id))
    else:
        cache.delete_memoized(api_services)


# TODO - Break this into an API cache expiration
def update_stats():
    """Invalidate cached statistics page data."""

    from scoring_engine.web.views.stats import home

    cache.delete_memoized(home)
