import colorsys
import itertools
import random
from collections import defaultdict

from sqlalchemy import Column, Integer, String, desc, func
from sqlalchemy.orm import relationship

from scoring_engine.db import db
from scoring_engine.models.base import Base
from scoring_engine.models.check import Check


# Curated palette: medium-saturation, medium-lightness colors that maintain
# WCAG AA contrast (4.5:1) on both dark (#0a0a0a–#161616) and light
# (#fafafa–#ffffff) backgrounds across all visual themes.
_TEAM_COLORS = [
    "#5b9cf6",  # blue
    "#e8656d",  # red
    "#4caf7d",  # green
    "#b388f2",  # purple
    "#e6a030",  # amber
    "#50bfc9",  # cyan
    "#e56aab",  # magenta
    "#d4a63a",  # gold
    "#6db0ef",  # light blue
    "#6ecf8a",  # lime
    "#f08080",  # salmon
    "#a07ee8",  # lavender
    "#e88e4a",  # orange
    "#41b86a",  # bright green
    "#82c4f0",  # sky
    "#d47a35",  # dark orange
    "#9ca8b4",  # silver
    "#d35a93",  # rose
    "#3da854",  # forest green
    "#7c5dcf",  # violet
    "#d8882e",  # tangerine
    "#3dbcc4",  # teal
    "#d66b70",  # coral
    "#8896a5",  # gray
    "#c49028",  # dark gold
    "#5cb88a",  # mint
    "#c86acc",  # orchid
    "#5ca4e8",  # cornflower
    "#dbb84a",  # yellow
    "#cf6666",  # indian red
    "#44bec8",  # light teal
    "#8cc45e",  # light green
]

# Track which palette colors have been assigned this session
_palette_index = 0
from scoring_engine.models.inject import Inject, InjectRubricScore
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service


def _get_rank_from_scores(scores, target_id, default=1):
    """
    Get rank for target_id from list of (id, score) tuples.
    Handles ties: same score = same rank (e.g., [100, 90, 90, 80] -> [1, 2, 2, 4]).
    Returns default if scores is empty or target_id not in scores.
    """
    if not scores:
        return default

    team_ids = [s[0] for s in scores]
    if target_id not in team_ids:
        return default

    # scores are already sorted descending by the query
    current_rank = 1
    prev_score = None
    for i, (item_id, score) in enumerate(scores):
        if prev_score is not None and score < prev_score:
            current_rank = i + 1
        if item_id == target_id:
            return current_rank
        prev_score = score
    return default


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    color = Column(String(10), nullable=False)
    services = relationship("Service", back_populates="team", lazy="joined")
    users = relationship("User", back_populates="team", lazy="joined")
    injects = relationship("Inject", back_populates="team", lazy="joined")
    rgb_color = Column(String(30))

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.rgb_color = self._next_color()

    @staticmethod
    def _next_color():
        """Pick the next distinct color from the curated palette, or generate a random vibrant one."""
        global _palette_index
        if _palette_index < len(_TEAM_COLORS):
            hex_color = _TEAM_COLORS[_palette_index]
            _palette_index += 1
            return hex_color
        # Fallback: random color with constrained HSL for dark-bg readability
        h = random.random()
        s = random.uniform(0.6, 0.9)
        l = random.uniform(0.55, 0.75)
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))

    @property
    def current_score(self):
        """
        Calculate current score from successful checks.
        WARNING: This performs a DB query on each access. Consider caching results
        or using bulk queries when accessing scores for multiple teams.
        """
        score = (
            db.session.query(func.sum(Service.points))
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
        """
        Calculate current inject score from graded injects.
        WARNING: This performs a DB query on each access. Consider caching results
        or using bulk queries when accessing scores for multiple teams.
        """
        score = (
            db.session.query(func.sum(InjectRubricScore.score))
            .join(Inject)
            .filter(Inject.team_id == self.id)
            .filter(Inject.status == "Graded")
            .scalar()
        )
        if not score:
            return 0
        return score

    @property
    def place(self):
        """
        Calculate team's current place/rank based on scores.
        WARNING: This queries ALL teams and their scores on EVERY access!
        This is very expensive - avoid calling in loops or templates.
        For bulk operations, calculate ranks once and cache/pass the results.
        See scoring_engine/web/views/api/overview.py for an efficient batch implementation.
        """
        scores = (
            db.session.query(
                Service.team_id,
                func.sum(Service.points).label("score"),
            )
            .join(Check)
            .filter(Check.result.is_(True))
            .group_by(Service.team_id)
            .order_by(desc("score"))
            .all()
        )

        # Scores are already sorted descending by the query
        # Returns 1 if no scores or team not in list
        return _get_rank_from_scores(scores, self.id, default=1)

    @property
    def is_red_team(self):
        return self.color == "Red"

    @property
    def is_white_team(self):
        return self.color == "White"

    @property
    def is_blue_team(self):
        return self.color == "Blue"

    # Adjectives and animals for anonymous team names
    # 50 adjectives × 30 animals = 1500 unique combinations
    _ADJECTIVES = [
        "Swift", "Brave", "Mighty", "Silent", "Cunning",
        "Bold", "Fierce", "Noble", "Stealthy", "Shadow",
        "Iron", "Golden", "Crystal", "Storm", "Frost",
        "Crimson", "Thunder", "Phantom", "Blazing", "Savage",
        "Lunar", "Solar", "Cyber", "Primal", "Spectral",
        "Ancient", "Emerald", "Sapphire", "Onyx", "Obsidian",
        "Rapid", "Rogue", "Eternal", "Mystic", "Stealth",
        "Elite", "Prime", "Alpha", "Omega", "Delta",
        "Apex", "Neon", "Arctic", "Inferno", "Venom",
        "Titan", "Dusk", "Tempest", "Wraith", "Chaos",
    ]
    _ANIMALS = [
        "Falcon", "Wolf", "Tiger", "Panther", "Eagle",
        "Bear", "Lion", "Viper", "Phoenix", "Dragon",
        "Hawk", "Cobra", "Raven", "Jaguar", "Shark",
        "Lynx", "Scorpion", "Stallion", "Raptor", "Hydra",
        "Griffin", "Serpent", "Kraken", "Mantis", "Barracuda",
        "Wyvern", "Basilisk", "Chimera", "Sphinx", "Cerberus",
    ]

    @classmethod
    def _get_anonymous_name(cls, index):
        """
        Generate a deterministic, unique anonymous name based on index.
        First 30 teams get unique adjectives and animals (1:1 mapping).
        Beyond 30, combinations cycle through all 1500 unique pairs.
        """
        num_animals = len(cls._ANIMALS)
        num_adjectives = len(cls._ADJECTIVES)

        if index < min(num_adjectives, num_animals):
            # First N teams get 1:1 unique adjective + animal
            adj_idx = index
            animal_idx = index
        else:
            # Beyond that, use divmod to generate unique combinations
            # This gives us num_adjectives × num_animals unique pairs
            adj_idx = index % num_adjectives
            animal_idx = (index // num_adjectives) % num_animals
            # Add offset to avoid repeating the first N combinations
            if adj_idx == animal_idx and adj_idx < min(num_adjectives, num_animals):
                animal_idx = (animal_idx + 1) % num_animals

        return f"{cls._ADJECTIVES[adj_idx]} {cls._ANIMALS[animal_idx]}"

    @classmethod
    def get_team_name_mapping(cls, anonymize=False, show_both=False):
        """
        Get a mapping of team IDs to display names.

        Args:
            anonymize: If True, returns only anonymous names (e.g., "Swift Falcon")
            show_both: If True, returns "RealName (Codename)" format for white team

        Returns: dict mapping team_id -> display_name
        """
        teams = db.session.query(cls).filter(cls.color == "Blue").order_by(cls.id).all()
        mapping = {}
        for idx, team in enumerate(teams):
            anon_name = cls._get_anonymous_name(idx)
            if anonymize:
                mapping[team.id] = anon_name
                mapping[team.name] = anon_name
            elif show_both:
                display_name = f"{team.name} ({anon_name})"
                mapping[team.id] = display_name
                mapping[team.name] = display_name
            else:
                mapping[team.id] = team.name
                mapping[team.name] = team.name
        return mapping

    def get_array_of_scores(self, max_round):
        round_scores = (
            db.session.query(
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
            db.session.query(func.sum(Service.points))
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
        return db.session.query(Team).filter(Team.color == "Blue").all()

    @staticmethod
    def get_all_red_teams():
        return db.session.query(Team).filter(Team.color == "Red").all()

    @staticmethod
    def get_all_rounds_results():
        results = {}
        results["scores"] = {}
        results["rounds"] = []

        rounds = []
        scores = {}
        blue_teams = db.session.query(Team).filter(Team.color == "Blue").all()
        last_round_obj = db.session.query(func.max(Round.number)).scalar()
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

    @property
    def total_sla_penalties(self):
        """
        Calculate total SLA penalties for this team across all services.
        """
        from scoring_engine.sla import calculate_team_total_penalties

        return calculate_team_total_penalties(self)

    @property
    def adjusted_score(self):
        """
        Get the team's score after applying SLA penalties.
        """
        from scoring_engine.sla import calculate_team_adjusted_score

        return calculate_team_adjusted_score(self)

    @property
    def sla_summary(self):
        """
        Get comprehensive SLA summary for this team.
        """
        from scoring_engine.sla import get_team_sla_summary

        return get_team_sla_summary(self)

    @property
    def services_with_sla_violations(self):
        """
        Get count of services with active SLA violations.
        """
        from scoring_engine.sla import get_sla_config

        config = get_sla_config()
        violations = 0
        for service in self.services:
            if service.consecutive_failures >= config.penalty_threshold:
                violations += 1
        return violations
