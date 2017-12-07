import json

from scoring_engine.models.team import Team
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.check import Check

from tests.scoring_engine.web.web_test import WebTest


class TestAPI(WebTest):

    def test_auth_required_admin_get_round_progress(self):
        self.verify_auth_required('/api/admin/get_round_progress')

    def test_auth_required_admin_get_teams(self):
        self.verify_auth_required('/api/admin/get_teams')

    def test_auth_required_admin_update_password(self):
        self.verify_auth_required_post('/api/admin/update_password')

    def test_auth_required_admin_add_user(self):
        self.verify_auth_required_post('/api/admin/add_user')

    def test_auth_required_profile_update_password(self):
        self.verify_auth_required_post('/api/profile/update_password')

    def test_auth_required_service_get_checks_id(self):
        self.verify_auth_required('/api/service/get_checks/1')

    '''
    def test_api_scoreboard_get_bar_data(self):
        resp = self.client.get('api/scoreboard/get_bar_data')
        assert resp.status_code == 200

    def test_api_scoreboard_get_line_data(self):
        resp = self.client.get('/api/scoreboard/get_line_data')
        assert resp.status_code == 200
    '''

    def test_overview_data_no_teams(self):
        overview_data = self.client.get('/api/overview/data')
        assert json.loads(overview_data.data.decode('utf8')) == {}

    def test_overview_data(self):
        # create 1 white team, 1 red team, 5 blue teams, 3 services per team, 5 checks per service
        # White Team
        self.session.add(Team(name="whiteteam", color="White"))
        # Red Team
        self.session.add(Team(name="redteam", color="Red"))
        self.session.commit()
        teams = []
        last_check_results = {
            "team1": {
                "FTPUpload": True,
                "DNS": True,
                "ICMP": True,
            },
            "team2": {
                "FTPUpload": False,
                "DNS": True,
                "ICMP": True,
            },
            "team3": {
                "FTPUpload": False,
                "DNS": True,
                "ICMP": False,
            },
            "team4": {
                "FTPUpload": True,
                "DNS": False,
                "ICMP": False,
            },
            "team5": {
                "FTPUpload": False,
                "DNS": False,
                "ICMP": False,
            },
        }
        for team_num in range(1, 6):
            team = Team(name="team" + str(team_num), color="Blue")
            icmp_service = Service(name="ICMP", team=team, check_name="ICMP IPv4 Check", ip_address="127.0.0.1")
            dns_service = Service(name="DNS", team=team, check_name="DNSCheck", ip_address="8.8.8.8", port=53)
            ftp_upload_service = Service(name='FTPUpload', team=team, check_name='FTPUploadCheck', ip_address='1.2.3.4', port=21)
            self.session.add(icmp_service)
            self.session.add(dns_service)
            self.session.add(ftp_upload_service)
            # 5 rounds of checks
            round_1 = Round(number=1)
            icmp_check_1 = Check(round=round_1, service=icmp_service, result=True, output="example_output")
            dns_check_1 = Check(round=round_1, service=dns_service, result=False, output="example_output")
            ftp_upload_check_1 = Check(round=round_1, service=ftp_upload_service, result=True, output="example_output")
            self.session.add(round_1)
            self.session.add(icmp_check_1)
            self.session.add(dns_check_1)
            self.session.add(ftp_upload_check_1)

            round_2 = Round(number=2)
            icmp_check_2 = Check(round=round_2, service=icmp_service, result=True, output="example_output")
            dns_check_2 = Check(round=round_2, service=dns_service, result=True, output="example_output")
            ftp_upload_check_2 = Check(round=round_2, service=ftp_upload_service, result=True, output="example_output")
            self.session.add(round_2)
            self.session.add(icmp_check_2)
            self.session.add(dns_check_2)
            self.session.add(ftp_upload_check_2)

            round_3 = Round(number=3)
            icmp_check_3 = Check(round=round_3, service=icmp_service, result=True, output="example_output")
            dns_check_3 = Check(round=round_3, service=dns_service, result=False, output="example_output")
            ftp_upload_check_3 = Check(round=round_3, service=ftp_upload_service, result=True, output="example_output")
            self.session.add(round_3)
            self.session.add(icmp_check_3)
            self.session.add(dns_check_3)
            self.session.add(ftp_upload_check_3)

            round_4 = Round(number=4)
            icmp_check_4 = Check(round=round_4, service=icmp_service, result=False, output="example_output")
            dns_check_4 = Check(round=round_4, service=dns_service, result=False, output="example_output")
            ftp_upload_check_4 = Check(round=round_4, service=ftp_upload_service, result=False, output="example_output")
            self.session.add(round_4)
            self.session.add(icmp_check_4)
            self.session.add(dns_check_4)
            self.session.add(ftp_upload_check_4)

            round_5 = Round(number=5)
            icmp_check_5 = Check(round=round_5, service=icmp_service, result=last_check_results[team.name]['ICMP'], output="example_output")
            dns_check_5 = Check(round=round_5, service=dns_service, result=last_check_results[team.name]['DNS'], output="example_output")
            ftp_upload_check_5 = Check(round=round_5, service=ftp_upload_service, result=last_check_results[team.name]['FTPUpload'], output="example_output")
            self.session.add(round_5)
            self.session.add(icmp_check_5)
            self.session.add(dns_check_5)
            self.session.add(ftp_upload_check_5)

            self.session.add(team)
            self.session.commit()
            teams.append(team)

        overview_data = self.client.get('/api/overview/data')
        overview_dict = json.loads(overview_data.data.decode('utf8'))
        expected_dict = {
            'team1': {
                'FTPUpload': {'passing': True, 'ip_address': '1.2.3.4', 'port': 21},
                'DNS': {'passing': True, 'ip_address': '8.8.8.8', 'port': 53},
                'ICMP': {'passing': True, 'ip_address': '127.0.0.1', 'port': 0}},
            'team2': {
                'FTPUpload': {'passing': False, 'ip_address': '1.2.3.4', 'port': 21},
                'DNS': {'passing': True, 'ip_address': '8.8.8.8', 'port': 53},
                'ICMP': {'passing': True, 'ip_address': '127.0.0.1', 'port': 0}},
            'team3': {
                'FTPUpload': {'passing': False, 'ip_address': '1.2.3.4', 'port': 21},
                'DNS': {'passing': True, 'ip_address': '8.8.8.8', 'port': 53},
                'ICMP': {'passing': False, 'ip_address': '127.0.0.1', 'port': 0}},
            'team4': {
                'FTPUpload': {'passing': True, 'ip_address': '1.2.3.4', 'port': 21},
                'DNS': {'passing': False, 'ip_address': '8.8.8.8', 'port': 53},
                'ICMP': {'passing': False, 'ip_address': '127.0.0.1', 'port': 0}},
            'team5': {
                'FTPUpload': {'passing': False, 'ip_address': '1.2.3.4', 'port': 21},
                'DNS': {'passing': False, 'ip_address': '8.8.8.8', 'port': 53},
                'ICMP': {'passing': False, 'ip_address': '127.0.0.1', 'port': 0}
            }
        }
        assert sorted(overview_dict.items()) == sorted(expected_dict.items())
