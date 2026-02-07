import os
from urllib.parse import urljoin

import pytest
import requests
from requests.exceptions import RequestException

BASE_URL = os.environ.get("SCORINGENGINE_WEBUI_BASE_URL", "https://nginx")
_REQUEST_TIMEOUT = float(os.environ.get("SCORINGENGINE_WEBUI_TIMEOUT", "5"))


def _build_url(page):
    base = BASE_URL if BASE_URL.endswith("/") else f"{BASE_URL}/"
    return urljoin(base, page)


def _skip_if_unreachable():
    try:
        response = requests.get(_build_url(""), verify=False, timeout=_REQUEST_TIMEOUT)
        response.close()
    except RequestException as exc:
        pytest.skip(
            f"Web UI not reachable at {BASE_URL!r}: {exc}",
            allow_module_level=True,
        )


_skip_if_unreachable()


class TestWebUI(object):
    def get_page(self, page):
        return requests.get(_build_url(page), verify=False, timeout=_REQUEST_TIMEOUT)

    pages = [
        {
            "page": "",
            "matching_text": "Diamond",
        },
        {
            "page": "scoreboard",
        },
        {
            "page": "login",
            "matching_text": "Please sign in",
        },
        {
            "page": "about",
            "matching_text": "Use the following credentials to login",
        },
        {
            "page": "overview",
        },
        {"page": "api/overview/data"},
    ]

    @pytest.mark.parametrize("page_data", pages)
    def test_page(self, page_data):
        resp = self.get_page(page_data["page"])
        assert resp.status_code == 200
        if "matching_text" in page_data:
            assert page_data["matching_text"] in resp.text
