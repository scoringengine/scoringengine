import pytest

def pytest_addoption(parser):
    parser.addoption("--scheme", action="store", default="")
    parser.addoption("--hostip", action="store", default="")
    parser.addoption("--hostname", action="store", default="")
    parser.addoption("--hostport", action="store", default="")
    parser.addoption("--basepath", action="store", default="")
    parser.addoption("--username", action="store", default="")
    parser.addoption("--password", action="store", default="")

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, pytestconfig):
    host_ip = pytestconfig.getoption("--hostip")
    host_name = pytestconfig.getoption("--hostname")

    # We only apply the rule if a hostip is actually provided
    if host_ip and host_name:
        return {
            **browser_type_launch_args,
            "args": [
                f"--host-resolver-rules=MAP {host_name} {host_ip}"
            ],
        }
    return browser_type_launch_args

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True
    }
