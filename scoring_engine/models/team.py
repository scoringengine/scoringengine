import random
from sqlalchemy import Column, Integer, String, desc
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base
from scoring_engine.models.round import Round


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    color = Column(String(10), nullable=False)
    services = relationship("Service", back_populates="team")
    users = relationship("User", back_populates="team")
    rgb_color = Column(String())

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.rgb_color = "rgba(%s, %s, %s, 1)" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    @property
    def current_score(self):
        total_score = 0
        for service in self.services:
            total_score += service.score_earned
        return total_score

    @property
    def place(self):
        sorted_blue_teams = sorted(self.blue_teams, key=lambda team: team.current_score, reverse=True)
        place = 0
        for index, team in enumerate(sorted_blue_teams):
            if self.id == team.id:
                place = index + 1
        return place

    @property
    def is_red_team(self):
        return self.color == 'Red'

    @property
    def is_white_team(self):
        return self.color == 'White'

    @property
    def is_blue_team(self):
        return self.color == 'Blue'

    @property
    def blue_teams(self):
        return Team.get_all_blue_teams()

    def get_array_of_scores(self, max_round):
        scores = [0]
        overall_score = 0
        for round_num in range(1, max_round + 1):
            current_round_score = 0
            for service in self.services:
                if service.check_result_for_round(round_num) is True:
                    current_round_score += service.points

            overall_score += current_round_score
            scores.append(overall_score)
        return scores

    def get_round_scores(self, round_num):
        if round_num == 0:
            return 0
        round_obj = Round.query.filter(Round.number == round_num).all()[0]
        round_score = 0
        for check in round_obj.checks:
            if check.service.team == self:
                if check.result is True:
                    round_score += check.service.points
        return round_score

    @staticmethod
    def get_all_blue_teams():
        return Team.query.filter(Team.color == 'Blue').all()

    @staticmethod
    def get_all_rounds_results():
        results = {}
        results['scores'] = {}
        results['rounds'] = []

        rounds = []
        scores = {}
        blue_teams = Team.query.filter(Team.color == 'Blue').all()
        last_round = Round.query.order_by(Round.number.desc()).first().number
        for round_num in range(0, last_round + 1):
            rounds.append("Round " + str(round_num))

        rgb_colors = {}
        for team in blue_teams:
            scores[team.name] = team.get_array_of_scores(last_round)
            rgb_colors[team.name] = team.rgb_color

        results['rounds'] = rounds
        results['scores'] = scores
        results['rgb_colors'] = rgb_colors

        return results
