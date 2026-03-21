"""
Test factory functions for creating model objects with sensible defaults.

Usage:
    from tests.scoring_engine.factories import (
        make_team, make_user, make_service, make_round, make_check,
        make_environment, make_three_teams_with_users,
    )

Each factory:
  - Auto-generates unique names when none are given.
  - Creates missing parent objects (e.g. ``make_user()`` creates a Blue team).
  - Adds + commits by default (pass ``commit=False`` to defer).
"""

import itertools

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

_counter = itertools.count(1)


def _next_id():
    return next(_counter)


# ---------------------------------------------------------------------------
# Core factories
# ---------------------------------------------------------------------------


def make_team(name=None, color="Blue", commit=True):
    n = _next_id()
    if name is None:
        name = f"{color} Team {n}"
    team = Team(name=name, color=color)
    db.session.add(team)
    if commit:
        db.session.commit()
    return team


def make_user(username=None, password="testpass", team=None, commit=True):
    n = _next_id()
    if team is None:
        team = make_team(commit=False)
    if username is None:
        username = f"user{n}"
    user = User(username=username, password=password, team=team)
    db.session.add(user)
    if commit:
        db.session.commit()
    return user


def make_service(name=None, team=None, check_name="ICMPCheck", host="127.0.0.1", port=1234, commit=True):
    n = _next_id()
    if team is None:
        team = make_team(commit=False)
    if name is None:
        name = f"Service {n}"
    service = Service(name=name, team=team, check_name=check_name, host=host, port=port)
    db.session.add(service)
    if commit:
        db.session.commit()
    return service


def make_environment(service=None, matching_content="*", commit=True):
    if service is None:
        service = make_service(commit=False)
    env = Environment(service=service, matching_content=matching_content)
    db.session.add(env)
    if commit:
        db.session.commit()
    return env


def make_round(number=None, commit=True, **kwargs):
    if number is None:
        number = _next_id()
    round_obj = Round(number=number, **kwargs)
    db.session.add(round_obj)
    if commit:
        db.session.commit()
    return round_obj


def make_check(service=None, round_obj=None, result=True, output="", commit=True):
    if service is None:
        service = make_service(commit=False)
    if round_obj is None:
        round_obj = make_round(commit=False)
    check = Check(service=service, round=round_obj, result=result, output=output)
    db.session.add(check)
    if commit:
        db.session.commit()
    return check


# ---------------------------------------------------------------------------
# Convenience shortcuts
# ---------------------------------------------------------------------------


def make_white_user(username=None, password="testpass", commit=True):
    team = make_team(color="White", commit=False)
    return make_user(username=username, password=password, team=team, commit=commit)


def make_blue_user(username=None, password="testpass", commit=True):
    team = make_team(color="Blue", commit=False)
    return make_user(username=username, password=password, team=team, commit=commit)


def make_red_user(username=None, password="testpass", commit=True):
    team = make_team(color="Red", commit=False)
    return make_user(username=username, password=password, team=team, commit=commit)


def make_three_teams_with_users(password="testpass", commit=True):
    """Create White/Blue/Red teams each with one user.

    Returns a dict: {"white_team", "blue_team", "red_team",
                     "white_user", "blue_user", "red_user"}
    """
    white_team = Team(name="White Team", color="White")
    blue_team = Team(name="Blue Team", color="Blue")
    red_team = Team(name="Red Team", color="Red")
    db.session.add_all([white_team, blue_team, red_team])
    db.session.flush()

    white_user = User(username="whiteuser", password=password, team=white_team)
    blue_user = User(username="blueuser", password=password, team=blue_team)
    red_user = User(username="reduser", password=password, team=red_team)
    db.session.add_all([white_user, blue_user, red_user])
    if commit:
        db.session.commit()

    return {
        "white_team": white_team,
        "blue_team": blue_team,
        "red_team": red_team,
        "white_user": white_user,
        "blue_user": blue_user,
        "red_user": red_user,
    }
