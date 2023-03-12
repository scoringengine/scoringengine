from tests.scoring_engine.web.web_test import WebTest
from tests.scoring_engine.helpers import generate_sample_model_tree


class TestServices(WebTest):

    def set_team_color(self, team, color):
        team.color = color
        self.session.add(team)
        self.session.commit()

    def set_blue_team(self, team):
        self.set_team_color(team, 'Blue')

    def set_white_team(self, team):
        self.set_team_color(team, 'White')

    def test_auth_required_services(self):
        self.verify_auth_required('/services')

    def test_auth_required_service_id(self):
        self.verify_auth_required('/service/1')

    def test_normal_services(self):
        user = self.create_default_user()
        service = generate_sample_model_tree('Service', self.session)
        self.set_blue_team(user.team)
        service.team = user.team
        self.session.add(service)
        self.session.commit()
        resp = self.auth_and_get_path('/services')
        assert resp.status_code == 200
        assert self.mock_obj.call_args == self.build_args('services.html')

    def test_unauthorized_services(self):
        user = self.create_default_user()
        service = generate_sample_model_tree('Service', self.session)
        self.set_white_team(user.team)
        service.team = user.team
        self.session.add(service)
        self.session.commit()
        resp = self.auth_and_get_path('/services')
        assert resp.status_code == 302

    def test_normal_service_id(self):
        user = self.create_default_user()
        service = generate_sample_model_tree('Service', self.session)
        self.set_blue_team(user.team)
        service.team = user.team
        self.session.add(service)
        self.session.commit()
        resp = self.auth_and_get_path('/service/1')
        assert resp.status_code == 200

    def test_unauthorized_service_id(self):
        self.create_default_user()
        resp = self.auth_and_get_path('/service/1')
        assert resp.status_code == 302
