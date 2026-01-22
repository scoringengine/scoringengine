import ranking

from sqlalchemy import Column, Integer, String, ForeignKey, desc, func
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base
from scoring_engine.models.check import Check
from scoring_engine.db import db


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
        """
        Get check result for a specific round.
        Optimized to use a DB query instead of loading all checks into memory.
        """
        from scoring_engine.models.round import Round

        check = (
            db.session.query(Check)
            .join(Round)
            .filter(Check.service_id == self.id)
            .filter(Round.number == round_num)
            .first()
        )
        if check:
            return check.result
        return False

    def last_check_result(self):
        """
        Get the result of the most recent check for this service.
        Uses a DB query to avoid session/lazy loading issues.
        """
        last_check = (
            db.session.query(Check)
            .filter(Check.service_id == self.id)
            .order_by(desc(Check.id))
            .first()
        )
        if last_check:
            return last_check.result
        return None

    @property
    def checks_reversed(self):
        return (
            db.session.query(Check)
            .filter(Check.service_id == self.id)
            .order_by(desc(Check.round_id))
            .all()
        )

    @property
    def rank(self):
        """
        Calculate this service's rank among all services with the same name.
        WARNING: This queries ALL services with this name on EVERY access!
        Avoid calling in loops. For bulk operations, calculate ranks in batch
        (see scoring_engine/web/views/api/team.py:42-62 for efficient implementation).
        """
        scores = (
            db.session.query(
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
        """
        Calculate total score earned by this service.
        WARNING: Performs DB query on each access. Cache when used multiple times.
        """
        return (
            db.session.query(Check)
            .filter(Check.service_id == self.id)
            .filter(Check.result.is_(True))
            .count()
        ) * self.points

    @property
    def max_score(self):
        """
        Calculate maximum possible score for this service.
        WARNING: Performs DB query on each access. Cache when used multiple times.
        """
        return (
            db.session.query(Check).filter(Check.service_id == self.id).count()
        ) * self.points

    @property
    def percent_earned(self):
        if self.max_score == 0:
            return 0
        return int((self.score_earned / self.max_score) * 100)

    @property
    def last_ten_checks(self):
        """
        Get the last 10 checks for this service in reverse chronological order.
        Optimized to use a DB query with LIMIT instead of loading all checks into memory.
        """
        return (
            db.session.query(Check)
            .filter(Check.service_id == self.id)
            .order_by(desc(Check.id))
            .limit(10)
            .all()
        )
