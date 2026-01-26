"""Integration test configuration and fixtures."""

import pytest


@pytest.fixture(scope='session', autouse=True)
def setup_integration_db(app_context):
    """
    Set up integration test database.
    Runs once per test session after the app context is created.
    """
    from tests.integration.db_setup import ensure_integration_data
    
    # Now that app context exists, set up the integration data
    ensure_integration_data()
