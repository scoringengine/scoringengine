import random

from scoring_engine.models.user import User
from scoring_engine.models.team import Team
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property


def populate_sample_data(session):
    team = Team(name="Blue Team 1", color="Blue")
    session.add(team)
    service = Service(name="Example Service 1", team=team, check_name="ICMP IPv4 Check", host='127.0.0.1')
    session.add(service)
    round_1 = Round(number=1)
    session.add(round_1)
    check_1 = Check(service=service, result=True, output='Good output', round=round_1)
    session.add(check_1)

    round_2 = Round(number=2)
    session.add(round_2)
    check_2 = Check(service=service, result=False, output='Bad output', round=round_2)
    session.add(check_2)
    session.commit()
    return team


def generate_sample_model_tree(model, session):
    # Team
    team = Team(name="Team 1", color="Blue")
    session.add(team)
    session.commit()
    if model == 'Team':
        return team

    # Users
    user = User(username="testuser" + str(random.randrange(10000)), password="catdog", team=team)
    session.add(user)
    session.commit()
    if model == 'User':
        return user

    # Services
    service = Service(name="ICMP IPv4", team=team, check_name="ICMP IPv4 Check", host='127.0.0.1')
    session.add(service)
    session.commit()
    if model == 'Service':
        return service

    # Environments
    environment = Environment(service=service, matching_content='*')
    session.add(environment)
    session.commit()
    if model == 'Environment':
        return environment

    # Properties
    property_obj = Property(name="testproperty", value="testvalue", environment=environment)
    session.add(property_obj)
    session.commit()
    if model == 'Property':
        return property_obj

    # Rounds
    round_obj = Round(number=1)
    session.add(round_obj)
    session.commit()
    if model == 'Round':
        return round_obj

    # Checks
    check = Check(round=round_obj, service=service)
    session.add(check)
    session.commit()
    if model == 'Check':
        return check
