from unittest.mock import call, patch

import pytest

from scoring_engine import cache_helper
from scoring_engine.web.views.api import overview


@pytest.mark.skipif(
    not hasattr(cache_helper, "delete_overview_data"),
    reason="delete_overview_data not available",
)
def test_delete_overview_data_clears_overview_cache():
    with patch("scoring_engine.cache_helper.cache.delete_memoized") as mock_delete:
        cache_helper.delete_overview_data()

    expected_calls = [
        call(overview.overview_data),
        call(overview.overview_get_columns),
        call(overview.overview_get_data),
        call(overview.overview_get_round_data),
    ]
    assert mock_delete.call_args_list == expected_calls


skip_update_overview = not hasattr(cache_helper, "update_overview_data") or not hasattr(
    overview, "update_caches"
)


@pytest.mark.skipif(
    skip_update_overview,
    reason="update_overview_data or update_caches not available",
)
def test_update_overview_data_triggers_update_caches():
    with patch("scoring_engine.web.views.api.overview.update_caches") as update_caches:
        cache_helper.update_overview_data()
    update_caches.assert_called_once_with()
