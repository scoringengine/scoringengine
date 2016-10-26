import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.team import Team
from models.server import Server
from models.service import Service
from models.check import Check
from db import DB


class TestCheck(object):
    def setup(self):
        self.db = DB()
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()

    def test_init_check(self):
        check = Check(round_num=1)
        assert check.id is None
        assert check.round_num == 1
        assert check.service is None
        assert check.service_id is None

    def test_basic_check(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        server = Server(name="Example Server", team=team)
        self.db.save(server)
        service = Service(name="Example Service", server=server, check_name="ICMP IPv4 Check")
        self.db.save(service)
        check = Check(round_num=1, service=service)
        self.db.save(check)
        assert check.id is not None
        assert check.service == service
        assert check.service_id == 1
