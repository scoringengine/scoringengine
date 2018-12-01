from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from copy import copy
from scoring_engine.models.base import Base
from scoring_engine.models.team import Team


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    check_name = Column(String(100), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="services")
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
