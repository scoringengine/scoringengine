"""Optional Playwright-based integration tests for the web UI."""

import os

import pytest

RUN_WEBUI = os.getenv("SCORINGENGINE_RUN_WEBUI_TESTS") == "1"

if not RUN_WEBUI:
    pytest.skip(
        "Playwright web UI integration tests are disabled by default; "
        "set SCORINGENGINE_RUN_WEBUI_TESTS=1 to enable.",
        allow_module_level=True,
    )

pytest.importorskip(
    "playwright.sync_api",
    reason=(
        "Playwright is required for web UI integration tests. "
        "Install optional requirements and set SCORINGENGINE_RUN_WEBUI_TESTS=1."
    ),
)

from playwright.sync_api import expect, sync_playwright


def _get_browser_context():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    return playwright, browser, context


class TestWebUIPlaywright:
    def test_login_page_renders(self):
        playwright, browser, context = _get_browser_context()
        page = context.new_page()
        try:
            page.goto("https://nginx/login")
            page.wait_for_load_state("networkidle")
            heading = page.get_by_role("heading", name="Please sign in")
            expect(heading).to_be_visible()
        finally:
            context.close()
            browser.close()
            playwright.stop()
