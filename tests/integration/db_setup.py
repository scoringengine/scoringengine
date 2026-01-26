"""Utility helpers for preparing the integration test database.

The real scoring engine is normally backed by MySQL and populated through a
number of external services.  The integration tests in this repository run in
isolation, so we create a minimal yet representative dataset backed by SQLite.
This module is imported by the integration tests during collection time to
ensure the database schema exists and contains deterministic data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List

import scoring_engine.models  # noqa: F401 – ensure models are registered with SQLAlchemy
from scoring_engine.db import delete_db, init_db, db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team

# Test expectations (mirroring the constants in ``test_integrations.py``)
_NUM_BLUE_TEAMS = 5
_NUM_ROUNDS = 5
_SERVICES_PER_TEAM = 15
_SERVICE_POINTS: List[int] = [125] + [100] * (_SERVICES_PER_TEAM - 1)

# A deterministic list of service names.  Each team receives a uniquely named
# instance of every service in this sequence to make debugging test failures
# easier.  The specific strings are not important, but a varied set mirrors the
# production data set that the original integration tests exercised.
_SERVICE_NAMES: List[str] = [
    "DNS",
    "HTTP",
    "HTTPS",
    "SSH",
    "SMTP",
    "IMAP",
    "POP3",
    "FTP",
    "SFTP",
    "SNMP",
    "RDP",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "VPN",
]


def _iter_service_definitions() -> Iterable[tuple[str, int]]:
    """Yield service names paired with their point values."""

    for name, points in zip(_SERVICE_NAMES, _SERVICE_POINTS):
        yield name, points


def _seed_rounds() -> List[Round]:
    """Create ``Round`` rows for the configured number of rounds."""

    rounds = [Round(number=idx) for idx in range(1, _NUM_ROUNDS + 1)]
    db.session.add_all(rounds)
    return rounds


def _seed_team(team_index: int, rounds: Iterable[Round]) -> None:
    """Populate a single blue team, its services and their checks."""

    team = Team(name=f"Blue Team {team_index}", color="Blue")
    db.session.add(team)
    db.session.flush()  # Ensure ``team.id`` is populated for relationship wiring

    for service_position, (base_name, points) in enumerate(_iter_service_definitions(), start=1):
        service = Service(
            name=f"{base_name} {team_index}",
            check_name=f"{base_name.lower()}_check",
            team=team,
            host=f"10.{team_index}.{service_position}.10",
            port=1000 + service_position,
            worker_queue="main",
        )
        service.points = points
        db.session.add(service)
        db.session.flush()

        for round_obj in rounds:
            db.session.add(
                Check(
                    round=round_obj,
                    service=service,
                    result=True,
                    output="All checks passed",
                    reason="",
                    command="noop",
                    completed=True,
                    completed_timestamp=datetime.now(timezone.utc),
                )
            )


def ensure_integration_data() -> None:
    """Reset the database and insert deterministic integration test data."""

    # Recreate the schema from scratch to avoid any persistent state between
    # test runs.  ``delete_db`` is safe to call even if the database is empty
    # because all models are imported above.
    delete_db()
    init_db()

    rounds = _seed_rounds()

    for team_index in range(1, _NUM_BLUE_TEAMS + 1):
        _seed_team(team_index, rounds)

    db.session.commit()
