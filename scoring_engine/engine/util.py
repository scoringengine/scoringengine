from typing import List

from scoring_engine.db import session
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.score import Score
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting


def update_scores() -> List[int]:
    """Update the scores of any teams that are listed in the teams_to_update setting.

    :return: A list of the IDs for teams whose scores were updated.
    :rtype: List[int]
    """
    # Get the list of team IDs
    teams_to_update = session.query(Setting).filter_by(name="teams_to_update").first()
    if teams_to_update is None:
        return []  # If the setting doesn't exist, skip it
    team_string = teams_to_update.value
    teams = [team_id for team_id in team_string.split(",")]

    for team in teams:
        # Update all rounds
        update_team_score(team, 1, Round.get_last_round_num())

    # Clear the team queue
    teams_to_update = ''
    session.commit()
    return teams


def update_team_score(
    team_id: int, first_round: int, last_round: int, add: bool = False
) -> None:
    """Update the scores of a specific team.

    Note that it doesn't really make sense to perform an update that doesn't continue
    all the way to the most recent round of scoring, since that will be used as the
    basis for the team's score for the next round.

    :param team_id: The ID of the team whose scores should be updated.
    :type team_id: int
    :param first_round: The first round that scores will be recalculated for.
    :type first_round: int
    :param last_round: The last round (inclusive) that scores will be recalculated for.
    :type last_round: int
    :param add: Whether to add new score objects if they don't exist. Defaults to False.
    :tpe add: bool
    """
    # Validate the first and last round
    if first_round < 1:
        first_round = 1
    max_round = Round.get_last_round_num()  # save value so we only it database once
    if last_round > max_round:
        last_round = max_round

    # Get score of previous round
    score = 0
    if first_round > 1:
        prev_round = session.query(Round).filter_by(number=(first_round - 1)).first()
        prev_score = (
            session.query(Score)
            .filter_by(team_id=team_id, round_id=prev_round.id)
            .first()
        )
        score = prev_score.value

    # Get all services for the team
    services = session.query(Service).filter_by(team_id=team_id).all()

    # Iterate through each round
    for round_num in range(first_round, last_round + 1):
        round_obj = session.query(Round).filter_by(number=round_num).first()

        # Determine the check result for each service
        for service_obj in services:
            # Get the service's check
            check_obj = (
                session.query(Check)
                .filter_by(service_id=service_obj.id, round_id=round_obj.id)
                .first()
            )
            if check_obj.result:
                score += service_obj.points

        # Update the round's score
        score_obj = (
            session.query(Score)
            .filter_by(team_id=team_id, round_id=round_obj.id)
            .first()
        )
        if (score_obj is None) and add:
            score_obj = Score(value=score, team_id=team_id, round=round_obj)
            session.add(score_obj)
        elif score_obj is not None:
            score_obj.value = score
        session.commit()
