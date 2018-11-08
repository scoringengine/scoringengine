import requests
import pytest


class TestWebUI(object):
    def get_page(self, page):
        return requests.get('https://nginx/{0}'.format(page), verify=False)

    pages = [
        {
            'page': '',
            'matching_text': 'Diamond',
        },
        {
            'page': 'scoreboard',
        },
        {
            'page': 'login',
            'matching_text': 'Please sign in',
        },
        {
            'page': 'about',
            'matching_text': 'Use the following credentials to login',
        },
        {
            'page': 'overview',
        },
        {
            'page': 'api/overview/data'
        }
    ]

    @pytest.mark.parametrize("page_data", pages)
    def test_page(self, page_data):
        resp = self.get_page(page_data['page'])
        assert resp.status_code == 200
        if 'matching_text' in page_data:
            assert page_data['matching_text'] in resp.text
