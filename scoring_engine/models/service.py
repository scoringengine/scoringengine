import ranking

from copy import copy
from sqlalchemy import Column, Integer, String, ForeignKey, desc, func
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base
from scoring_engine.models.check import Check
from scoring_engine.db import session


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    check_name = Column(String(100), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="services", lazy="joined")
    checks = relationship("Check", back_populates="service")
    accounts = relationship("Account", back_populates="service")
    points = Column(Integer, default=100)
    environments = relationship("Environment", back_populates="service")
    host = Column(String(50), nullable=False)
    port = Column(Integer, default=0)
    worker_queue = Column(String(50), default="main")

    def check_result_for_round(self, round_num):
        for check in self.checks:
            if check.round.number == round_num:
                return check.result
        return False

    def last_check_result(self):
        if not self.checks:
            return None
        return self.checks[-1].result

    @property
    def checks_reversed(self):
        return (
            session.query(Check)
            .filter(Check.service_id == self.id)
            .order_by(desc(Check.round_id))
            .all()
        )

    @property
    def rank(self):
        scores = (
            session.query(
                Service.team_id,
                func.sum(Service.points).label("score"),
            )
            .join(Check)
            .filter(Check.result.is_(True))
            .filter(Service.name == self.name)
            .group_by(Service.team_id)
            .order_by(desc("score"))
            .all()
        )

        # If there are no scores, return None
        if not scores:
            return None

        ranks = list(
            ranking.Ranking(scores, start=1, key=lambda x: x[1]).ranks()
        )  # [1, 2, 2, 4, 5]
        team_ids = [x[0] for x in scores]  # [5, 3, 6, 4, 7]

        # If the team is not in the list, return None
        if self.team_id not in team_ids:
            return None

        return ranks[team_ids.index(self.team_id)]

    @property
    def score_earned(self):
        return (
            session.query(Check)
            .filter(Check.service_id == self.id)
            .filter(Check.result.is_(True))
            .count()
        ) * self.points

    @property
    def max_score(self):
        return (
            session.query(Check).filter(Check.service_id == self.id).count()
        ) * self.points

    @property
    def percent_earned(self):
        if self.max_score == 0:
            return 0
        return int((self.score_earned / self.max_score) * 100)

    @property
    def last_ten_checks(self):
        reverse_checks = copy(self.checks)
        reverse_checks.reverse()
        return reverse_checks[:10]
