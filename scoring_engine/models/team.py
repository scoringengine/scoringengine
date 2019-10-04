import random
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base
from scoring_engine.models.round import Round
from scoring_engine.models.score import Score
from scoring_engine.models.setting import Setting
from scoring_engine.db import session


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    color = Column(String(10), nullable=False)
    services = relationship("Service", back_populates="team", lazy="joined")
    users = relationship("User", back_populates="team", lazy="joined")
    rgb_color = Column(String(30))
    scores = relationship('Score', back_populates="team")

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.rgb_color = "rgba(%s, %s, %s, 1)" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    @property
    def current_score(self):
        score = session.query(Score.value).filter(Score.team_id == self.id).join(Score.round).order_by(Round.number.desc()).first()
        if score is None:
            return 0
        else:
            # It returns a tuple that we want to unwrap
            return score[0]

    @property
    def place(self):
        sorted_blue_teams = sorted(Team.get_all_blue_teams(), key=lambda team: team.current_score, reverse=True)
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
        return self.color == 'Red'

    @property
    def is_white_team(self):
        return self.color == 'White'

    @property
    def is_blue_team(self):
        return self.color == 'Blue'

    def get_array_of_scores(self, max_round):
        result = [0]  # Round 0 score will always be zero, change my mind
        for score in self.scores:
            if score.round.number <= max_round:
                result.append(score.value)
        result.sort()
        return result

    def get_round_scores(self, round_num: int) -> int:
        """Get the number of points a team earned during a specific round.

        :param round_num: The number of the round to check.
        :type round_num: int
        :return: How many points the team earned during the specified round.
        :rtype: int
        """
        # TestTeam.test_get_round_scores requires we raise this exception
        if round_num > Round.get_last_round_num():
            raise IndexError()

        # Get the current score and the previous score so we can subtract the two
        round_score = 0
        prev_round_score = 0
        for score in self.scores:
            if score.round.number == round_num:
                round_score = score.value
            elif score.round.number == round_num - 1:
                prev_round_score = score.value

        return round_score - prev_round_score

    @staticmethod
    def get_all_blue_teams():
        return session.query(Team).filter(Team.color == 'Blue').all()

    @staticmethod
    def get_all_rounds_results():
        results = {}
        results['scores'] = {}
        results['rounds'] = []

        rounds = []
        scores = {}
        blue_teams = session.query(Team).filter(Team.color == 'Blue').all()
        last_round_obj = session.query(Round).order_by(Round.number.desc()).first()
        if last_round_obj:
            last_round = last_round_obj.number
            for round_num in range(0, last_round + 1):
                rounds.append("Round " + str(round_num))

            rgb_colors = {}
            team_names = []
            for team in blue_teams:
                scores[team.name] = team.get_array_of_scores(last_round)
                rgb_colors[team.name] = team.rgb_color
                team_names.append(team.name)
            results['team_names'] = team_names
            results['rgb_colors'] = rgb_colors

        results['rounds'] = rounds
        results['scores'] = scores

        return results

    def queue_update(self):
        """Queue a score update for this team.
        """
        teams_to_update = session.query(Setting).filter_by(name='teams_to_update').first()
        team_list = teams_to_update.value

        # Only add a preceeding comma if the list is not empty
        if team_list != '':
            team_list += ','

        team_list += str(self.id)
        teams_to_update.value = team_list
        session.commit()
