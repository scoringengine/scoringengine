from sqlalchemy import Column, Integer, String, ForeignKey, desc, func
from sqlalchemy.orm import relationship
from copy import copy
from scoring_engine.models.base import Base
from scoring_engine.models.check import Check
from scoring_engine.db import session


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    check_name = Column(String(100), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="services", lazy="joined")
    checks = relationship("Check", back_populates="service")
    accounts = relationship("Account", back_populates="service")
    points = Column(Integer, default=100)
    environments = relationship('Environment', back_populates="service")
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
        return sorted(self.checks, key=lambda check: check.round.number, reverse=True)

    @property
    def rank(self):
        scores = session.query(
            Service.team_id,
            func.sum(Service.points).label('score'),
        ) \
        .join(Check) \
        .filter(Check.result.is_(True)) \
        .group_by(Service.team_id) \
        .order_by(desc('score')) \
        .all()

        team_ranks = [x[0] for x in scores]
        place = team_ranks.index(self.team_id) + 1
        return place

        services = []
        for blue_team in Team.get_all_blue_teams():
            for service in blue_team.services:
                if self.name == service.name:
                    services.append(service)
        sorted_services = sorted(services, key=lambda service: service.score_earned, reverse=True)
        place = 0
        previous_place = 1
        for service in sorted_services:
            if not self.score_earned == service.score_earned:
                previous_place += 1
            if self.id == service.id:
                place = previous_place
        return place

    @property
    def score_earned(self):
        passed_checks = [check for check in self.checks if check.result is True]
        return len(passed_checks) * self.points

    @property
    def max_score(self):
        return len(self.checks) * self.points

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
