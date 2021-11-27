import itertools
import random
from sqlalchemy import Column, Integer, String, desc, func
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.db import session


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    color = Column(String(10), nullable=False)
    services = relationship("Service", back_populates="team", lazy="joined")
    users = relationship("User", back_populates="team", lazy="joined")
    rgb_color = Column(String(30))

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.rgb_color = "rgba(%s, %s, %s, 1)" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )

    @property
    def current_score(self):
        return (
            session.query(func.sum(Service.points))
            .select_from(Team)
            .join(Service)
            .join(Check)
            .filter(Service.team_id == self.id)
            .filter(Check.result.is_(True))
            .group_by(Service.team_id)
            .scalar()
        )

    @property
    def place(self):
        sorted_blue_teams = sorted(
            Team.get_all_blue_teams(), key=lambda team: team.current_score, reverse=True
        )
        place = 0
        previous_place = 1
        for team in sorted_blue_teams:
            if not self.current_score == team.current_score:
                previous_place += 1
            if self.id == team.id:
                place = previous_place
        return place

    @property
    def is_red_team(self):
        return self.color == "Red"

    @property
    def is_white_team(self):
        return self.color == "White"

    @property
    def is_blue_team(self):
        return self.color == "Blue"

    def get_array_of_scores(self, max_round):
        scores = [0]
        overall_score = 0

        round_scores = (
            session.query(
                func.sum(Service.points),
            )
            .join(Check)
            .join(Round)
            .filter(Service.team_id == self.id)
            .filter(Check.result.is_(True))
            .filter(Round.number <= max_round)
            .group_by(Check.round_id)
            .all()
        )

        # Accumulate the scores for each round based on previous round
        return list(itertools.accumulate([x[0] for x in round_scores]))

    def get_round_scores(self, round_num):
        if round_num == 0:
            return 0
        round_obj = session.query(Round).filter(Round.number == round_num).all()[0]
        round_score = 0
        for check in round_obj.checks:
            if check.service.team == self:
                if check.result is True:
                    round_score += check.service.points
        return round_score

    @staticmethod
    def get_all_blue_teams():
        return session.query(Team).filter(Team.color == "Blue").all()

    @staticmethod
    def get_all_rounds_results():
        results = {}
        results["scores"] = {}
        results["rounds"] = []

        rounds = []
        scores = {}
        blue_teams = session.query(Team).filter(Team.color == "Blue").all()
        last_round_obj = session.query(func.max(Round.number)).scalar()
        if last_round_obj:
            last_round = last_round_obj
            rounds = ["Round {}".format(x) for x in range(0, last_round + 1)]
            # for round_num in range(0, last_round + 1):
            #     rounds.append("Round " + str(round_num))

            rgb_colors = {}
            team_names = []
            for team in blue_teams:
                scores[team.name] = team.get_array_of_scores(last_round)
                rgb_colors[team.name] = team.rgb_color
                team_names.append(team.name)
            results["team_names"] = team_names
            results["rgb_colors"] = rgb_colors

        results["rounds"] = rounds
        results["scores"] = scores

        return results
