import random
from scoring_engine.models import *


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
    service = Service(name="ICMP IPv4", team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
    session.add(service)
    session.commit()
    if model == 'Service':
        return service

    # Environments
    environment = Environment(service=service, matching_regex='*')
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
