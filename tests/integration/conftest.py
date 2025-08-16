import pytest
import sys
import types

# Provide a minimal bcrypt stub so that the real dependency is not required
bcrypt_stub = types.ModuleType("bcrypt")
bcrypt_stub.__version__ = "0"
bcrypt_stub.gensalt = lambda: b""
bcrypt_stub.hashpw = lambda password, salt: b""
sys.modules.setdefault("bcrypt", bcrypt_stub)

from scoring_engine.db import session, init_db, delete_db
from scoring_engine.models.team import Team
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.check import Check

NUM_TEAMS = 2
NUM_SERVICES = 2
NUM_ROUNDS = 2
SERVICE_POINTS = 100

@pytest.fixture
def seeded_db():
    init_db(session)

    # create rounds
    rounds = [Round(number=i + 1) for i in range(NUM_ROUNDS)]
    session.add_all(rounds)
    session.commit()

    teams = []
    for t in range(NUM_TEAMS):
        team = Team(name=f"Blue{t + 1}", color="Blue")
        session.add(team)
        session.commit()
        for s in range(NUM_SERVICES):
            service = Service(
                name=f"service{s + 1}",
                check_name="dummy",
                host="localhost",
                port=0,
                team=team,
                points=SERVICE_POINTS,
            )
            session.add(service)
        session.commit()
        teams.append(team)

    # add checks for each round/service
    for rnd in rounds:
        for team in teams:
            for service in team.services:
                check = Check(round=rnd, service=service, result=True)
                session.add(check)
        session.commit()

    yield {
        "num_teams": NUM_TEAMS,
        "num_services": NUM_SERVICES,
        "num_rounds": NUM_ROUNDS,
        "service_points": SERVICE_POINTS,
    }

    delete_db(session)
