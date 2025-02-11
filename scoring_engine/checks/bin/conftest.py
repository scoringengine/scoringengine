import pytest

def pytest_addoption(parser):
    parser.addoption("--scheme", action="store", default="")
    parser.addoption("--hostip", action="store", default="")
    parser.addoption("--hostport", action="store", default="")
    parser.addoption("--basepath", action="store", default="")
    parser.addoption("--username", action="store", default="")
    parser.addoption("--password", action="store", default="")

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True
    }
