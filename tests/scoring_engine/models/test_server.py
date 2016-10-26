import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.team import Team
from models.server import Server
from models.service import Service
from db import DB


class TestServer(object):
    def setup(self):
        self.db = DB()
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()

    def test_init_server(self):
        server = Server(name="Example Server")
        assert server.id is None
        assert server.name == "Example Server"
        assert server.team is None
        assert server.team_id is None

    def test_basic_server(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        server = Server(name="Example Server", team=team)
        self.db.save(server)
        assert server.id is not None
        assert server.name == "Example Server"
        assert server.team == team
        assert server.team_id == 1

    def test_services(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        server = Server(name="Example Server", team=team)
        self.db.save(server)
        service_1 = Service(name="Example Service 1", server=server, check_name="ICMP IPv4 Check")
        self.db.save(service_1)
        service_2 = Service(name="Example Service 2", server=server, check_name="SSH IPv4 Check")
        self.db.save(service_2)
        assert server.services == [service_1, service_2]
