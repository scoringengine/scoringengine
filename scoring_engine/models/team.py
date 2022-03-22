import itertools
import random
import ranking

from collections import defaultdict
from sqlalchemy import Column, Integer, String, desc, func
from sqlalchemy.orm import relationship


from scoring_engine.models.base import Base
from scoring_engine.models.check import Check
from scoring_engine.models.inject import Inject
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
    inject = relationship("Inject", back_populates="team", lazy="joined")
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
        score = (
            session.query(func.sum(Service.points))
            .select_from(Team)
            .join(Service)
            .join(Check)
            .filter(Service.team_id == self.id)
            .filter(Check.result.is_(True))
            .scalar()
        )
        if not score:
            return 0
        return score

    @property
    def current_inject_score(self):
        score = (
            session.query(func.sum(Inject.score))
            .join(Team)
            .filter(Inject.team_id == self.id)
            .filter(Inject.status == "Graded")
            .scalar()
        )
        if not score:
            return 0
        return score

    @property
    def place(self):
        scores = (
            session.query(
                Service.team_id,
                func.sum(Service.points).label("score"),
            )
            .join(Check)
            .filter(Check.result.is_(True))
            .group_by(Service.team_id)
            .order_by(desc("score"))
            .all()
        )

        if scores:
            ranks = list(
                ranking.Ranking(scores, start=1, key=lambda x: x[1]).ranks()
            )  # [1, 2, 2, 4, 5]
            team_ids = [x[0] for x in scores]  # [5, 3, 6, 4, 7]

            return ranks[team_ids.index(self.id)]
        # Round 0, or no other scores available
        else:
            return 1

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
        round_scores = (
            session.query(
                Check.round_id,
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

        # Create default dict with 0 as default round value
        d = defaultdict(int)
        for k, v in round_scores:
            d[k] = v

        # Loop over all rounds and add 0 if not present
        # TODO - There has to be a better way to do this...
        for i in range(0, max_round + 1):
            d[i]

        # Accumulate the scores for each round based on previous round
        return list(itertools.accumulate([x[1] for x in sorted(d.items())]))

    # TODO - Can this be deprecated, it only exists in tests
    def get_round_scores(self, round_num):
        if round_num == 0:
            return 0

        score = (
            session.query(func.sum(Service.points))
            .join(Check)
            .join(Round)
            .filter(Service.team_id == self.id)
            .filter(Check.result.is_(True))
            .filter(Round.number == round_num)
            .group_by(Check.round_id)
            .scalar()
        )

        return score if score else 0

    @staticmethod
    def get_all_blue_teams():
        return session.query(Team).filter(Team.color == "Blue").all()

    @staticmethod
    def get_all_red_teams():
        return session.query(Team).filter(Team.color == "Red").all()

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
