import pytest

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.helpers import generate_sample_model_tree, populate_sample_data


class TestTeam:
    @pytest.mark.parametrize(
        "name,color,is_white,is_blue,is_red",
        [
            ("White Team", "White", True, False, False),
            ("Blue Team", "Blue", False, True, False),
            ("Red Team", "Red", False, False, True),
        ],
        ids=["white", "blue", "red"],
    )
    def test_init_team(self, name, color, is_white, is_blue, is_red):
        team = Team(name=name, color=color)
        assert team.name == name
        assert team.color == color
        assert team.id is None
        assert team.current_score == 0
        assert team.is_white_team is is_white
        assert team.is_blue_team is is_blue
        assert team.is_red_team is is_red

    def test_simple_save(self):
        white_team = Team(name="White Team", color="White")
        db.session.add(white_team)
        db.session.commit()
        assert white_team.id is not None
        assert len(db.session.query(Team).all()) == 1

    def test_multiple_saves(self):
        white_team = Team(name="White Team", color="White")
        db.session.add(white_team)
        blue_team = Team(name="Blue", color="Blue")
        db.session.add(blue_team)
        db.session.commit()
        assert len(db.session.query(Team).all()) == 2

    def test_services(self):
        team = generate_sample_model_tree("Team", db.session)
        service_1 = Service(name="Example Service 1", team=team, check_name="ICMP IPv4 Check", host="127.0.0.1")
        service_2 = Service(name="Example Service 2", team=team, check_name="SSH IPv4 Check", host="2.3.4.5")
        db.session.add(service_1)
        db.session.add(service_2)
        db.session.commit()
        assert team.services == [service_1, service_2]

    def test_users(self):
        team = generate_sample_model_tree("Team", db.session)
        user_1 = User(username="abcuser", password="abcpass", team=team)
        user_2 = User(username="testuser", password="testpass", team=team)
        db.session.add(user_1)
        db.session.add(user_2)
        db.session.commit()
        assert team.users == [user_1, user_2]

    def test_current_score(self):
        team = generate_sample_model_tree("Team", db.session)
        service_1 = Service(name="Example Service 1", team=team, check_name="ICMP IPv4 Check", host="127.0.0.1")
        db.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output="Good output")
        db.session.add(check_1)
        service_2 = Service(name="Example Service 2", team=team, check_name="SSH IPv4 Check", host="127.0.0.2")
        db.session.add(service_2)
        check_2 = Check(service=service_2, result=True, output="Good output")
        db.session.add(check_2)
        check_3 = Check(service=service_2, result=True, output="Good output")
        db.session.add(check_3)
        service_3 = Service(name="Example Service 3", team=team, check_name="SSH IPv4 Check", host="127.0.0.3")
        db.session.add(service_3)
        check_3 = Check(service=service_3, result=False, output="bad output")
        db.session.add(check_3)
        db.session.commit()
        assert team.current_score == 300

    def test_place(self):
        team_1 = Team(name="Blue Team 1", color="Blue")
        db.session.add(team_1)
        service_1 = Service(name="Example Service 1", team=team_1, check_name="ICMP IPv4 Check", host="127.0.0.1")
        db.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output="Good output")
        check_2 = Check(service=service_1, result=True, output="Good output")
        db.session.add(check_1)
        db.session.add(check_2)
        db.session.commit()

        team_2 = Team(name="Blue Team 2", color="Blue")
        db.session.add(team_2)
        service_1 = Service(name="Example Service 1", team=team_2, check_name="ICMP IPv4 Check", host="127.0.0.1")
        db.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output="Good output")
        check_2 = Check(service=service_1, result=True, output="Good output")
        db.session.add(check_1)
        db.session.add(check_2)
        db.session.commit()

        team_3 = Team(name="Blue Team 3", color="Blue")
        db.session.add(team_3)
        service_1 = Service(name="Example Service 1", team=team_3, check_name="ICMP IPv4 Check", host="127.0.0.1")
        db.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output="Good output")
        check_2 = Check(service=service_1, result=False, output="Bad output")
        db.session.add(check_1)
        db.session.add(check_2)
        db.session.commit()
        assert team_1.place == 1
        assert team_2.place == 1
        assert team_3.place == 3

    def test_place_round_zero(self):
        team_1 = Team(name="Blue Team 1", color="Blue")
        db.session.add(team_1)
        service_1 = Service(name="Example Service 1", team=team_1, check_name="ICMP IPv4 Check", host="127.0.0.1")
        db.session.add(service_1)
        db.session.commit()

        team_2 = Team(name="Blue Team 2", color="Blue")
        db.session.add(team_2)
        service_1 = Service(name="Example Service 1", team=team_2, check_name="ICMP IPv4 Check", host="127.0.0.1")
        db.session.add(service_1)
        db.session.commit()

        team_3 = Team(name="Blue Team 3", color="Blue")
        db.session.add(team_3)
        service_1 = Service(name="Example Service 1", team=team_3, check_name="ICMP IPv4 Check", host="127.0.0.1")
        db.session.add(service_1)
        db.session.commit()
        assert team_1.place == 1
        assert team_2.place == 1
        assert team_3.place == 1

    def test_get_array_of_scores(self):
        populate_sample_data(db.session)
        results = Team.get_all_rounds_results()
        assert "rounds" in results
        assert results["rounds"] == ["Round 0", "Round 1", "Round 2"]
        assert "rgb_colors" in results
        assert "Blue Team 1" in results["rgb_colors"]
        assert results["rgb_colors"]["Blue Team 1"].startswith("#")
        assert "scores" in results
        assert results["scores"] == {"Blue Team 1": [0, 100, 100]}

    def test_get_round_scores(self):
        team = populate_sample_data(db.session)
        assert team.get_round_scores(0) == 0
        assert team.get_round_scores(1) == 100
        assert team.get_round_scores(2) == 0
