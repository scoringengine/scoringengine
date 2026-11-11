"""Requirements every service check must meet.

Generated from the checks the engine actually discovers, so a new check is
covered automatically -- and fails here, naming itself, if it's missing a
piece -- without anyone maintaining a list of check names.
"""

import os
import re

import pytest

from scoring_engine.engine.basic_check import BasicCheck
from scoring_engine.engine.engine import Engine
from scoring_engine.engine.http_post_check import HTTPPostCheck
from tests.scoring_engine.checks.test_all_checks import CHECK_PARAMS

REPO = os.path.join(os.path.dirname(__file__), "..", "..", "..")
CHECKS_DIR = os.path.join(REPO, "scoring_engine", "checks")
DOCS_INDEX = os.path.join(REPO, "docs", "source", "checks.rst")

CHECKS = sorted(Engine.load_check_files(CHECKS_DIR), key=lambda c: c.__name__)
CHECK_IDS = [c.__name__ for c in CHECKS]


def _module_stem(check_class):
    # Engine loads check files without registering them in sys.modules, so use
    # the module name it assigned ("checks.ssh") rather than inspect.getfile.
    return check_class.__module__.rsplit(".", 1)[-1]


def _doc_candidates(stem):
    """Docs page(s) that may document a check module.

    Exact module name, the plain protocol for TLS variants (https -> http), or
    the family prefix for grouped checks (webapp_scoringengine -> webapp).
    """
    candidates = [stem]
    if stem.endswith("s"):
        candidates.append(stem[:-1])
    if "_" in stem:
        candidates.append(stem.split("_")[0])
    return candidates


def test_checks_are_discovered():
    assert len(CHECKS) >= 28


@pytest.mark.parametrize("check_class", CHECKS, ids=CHECK_IDS)
def test_check_is_a_basic_check_with_cmd(check_class):
    assert issubclass(check_class, BasicCheck)
    assert isinstance(getattr(check_class, "CMD", None), str) and check_class.CMD, "CMD must be a non-empty string"
    assert isinstance(check_class.required_properties, list)


@pytest.mark.parametrize("check_class", CHECKS, ids=CHECK_IDS)
def test_check_has_command_test(check_class):
    tested = {param.id for param in CHECK_PARAMS}
    assert check_class.__name__ in tested, (
        f"Add a pytest.param(..., id={check_class.__name__!r}) to CHECK_PARAMS in "
        "tests/scoring_engine/checks/test_all_checks.py"
    )


@pytest.mark.parametrize("check_class", CHECKS, ids=CHECK_IDS)
def test_check_is_documented(check_class):
    with open(DOCS_INDEX) as f:
        included = set(re.findall(r"^\.\. include:: checks/(\w+)\.rst$", f.read(), re.M))
    stem = _module_stem(check_class)
    documented = [c for c in _doc_candidates(stem) if c in included]
    assert documented, (
        f"Add docs/source/checks/{stem}.rst and include it in docs/source/checks.rst "
        f"(accepted pages: {', '.join(_doc_candidates(stem))})"
    )
    page = os.path.join(REPO, "docs", "source", "checks", documented[0] + ".rst")
    assert os.path.exists(page)


@pytest.mark.parametrize("check_class", CHECKS, ids=CHECK_IDS)
def test_command_test_covers_every_required_property(check_class):
    """The CHECK_PARAMS entry must supply each required property, so the
    command test actually renders the check rather than raising LookupError."""
    param = next((p for p in CHECK_PARAMS if p.id == check_class.__name__), None)
    if param is None:
        pytest.skip("covered by test_check_has_command_test")
    properties = param.values[1]
    assert set(properties) == set(check_class.required_properties)


def _quoted_placeholders(cmd):
    """Return the ``{N}`` placeholders in ``cmd`` that sit inside shell quotes.

    BasicCheck.command() shlex-quotes every argument. If the template also
    wraps the placeholder in quotes, the two sets cancel out ('{2}' becomes
    ''value''), so the value reaches the shell unquoted.
    """
    found = []
    quote = None
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if ch == "\\" and quote != "'":
            i += 2
            continue
        if quote is None and ch in "'\"":
            quote = ch
        elif ch == quote:
            quote = None
        elif quote is not None:
            match = re.match(r"\{\d+\}", cmd[i:])
            if match:
                found.append(match.group())
        i += 1
    return found


def test_quoted_placeholder_detection():
    assert _quoted_placeholders("medusa -u '{2}' -p {3}") == ["{2}"]
    assert _quoted_placeholders('curl --header "Host: {0}" {1}') == ["{0}"]
    assert _quoted_placeholders("ldapsearch -b {3} '(objectclass=Domain)' cn") == []
    assert _quoted_placeholders("medusa -u {2} -p {3}") == []


@pytest.mark.parametrize("check_class", CHECKS, ids=CHECK_IDS)
def test_cmd_does_not_quote_placeholders(check_class):
    # HTTPPostCheck URL-encodes its args instead of shell-quoting them, so its
    # templates must quote placeholders themselves.
    if issubclass(check_class, HTTPPostCheck):
        return
    quoted = _quoted_placeholders(check_class.CMD)
    assert not quoted, (
        f"{check_class.__name__}.CMD wraps {quoted} in quotes. BasicCheck.command() already "
        "shlex-quotes every argument, and the extra quotes cancel that out. Use a bare {N}."
    )
