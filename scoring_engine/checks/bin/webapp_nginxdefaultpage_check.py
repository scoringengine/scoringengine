#!/usr/bin/env python

# A scoring engine check that spins up a browser to check the HTML content of the nginx default page
# Note: It would never make sense to make such a simple "advanced web check" as this kind of test
#       should be used to test/validate website functionality by making use of playwright's interactivity
#       capabilities. This test is used as a sample and to assist with testing of the scoringengine 
#       project. Please refer to the webapp_scoringengine_check.py for a more realistic example scoring
#       check you might actually want to write.
#
# To install pip install pytest-playwright; playwright install chromium;

import re
from playwright.sync_api import Page, expect

def test_default_page_works(page: Page, request):
    scheme = request.config.getoption("--scheme")
    hostip = request.config.getoption("--hostip")
    hostport = request.config.getoption("--hostport")
    basepath = request.config.getoption("--basepath")

    page.goto(scheme + "://" + hostip + ":" + hostport + basepath)

    expect(page.locator('h1'), 'Nginx default welcome header is not present').to_have_text(re.compile("Welcome to nginx"))
