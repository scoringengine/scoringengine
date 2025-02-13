#!/usr/bin/env python

# A scoring engine check that logs into the scoringengine/scoringengine webapp
#
# To install pip install pytest-playwright; playwright install chromium;

import re
from playwright.sync_api import Page, expect

def test_signin_flow_works(page: Page, request):
    scheme = request.config.getoption("--scheme")
    hostip = request.config.getoption("--hostip")
    hostport = request.config.getoption("--hostport")
    basepath = request.config.getoption("--basepath")
    username = request.config.getoption("--username")
    password = request.config.getoption("--password")

    page.goto(scheme + "://" + hostip + ":" + hostport + basepath + "login")

    expect(page.get_by_role("heading", name="Please sign in"), 'Login form on /login did not render').to_be_visible()

    page.get_by_placeholder("Username").fill(username, timeout=2000)
    page.get_by_placeholder("Password").fill(password, timeout=2000)
    page.get_by_role("button", name="Sign in").click()

    expect(page, 'Login failed and/or did not correctly redirect to Services page after login').to_have_title(re.compile("Services"))
