import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.db import db
from scoring_engine.models.server import Server
from scoring_engine.models.service import Service

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree


class TestServer(object):
    def setup(self):
        self.db = db
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
        team = generate_sample_model_tree('Team', self.db)
        server = Server(name="Example Server", team=team)
        self.db.save(server)
        assert server.id is not None
        assert server.name == "Example Server"
        assert server.team == team
        assert server.team_id == team.id

    def test_services(self):
        server = generate_sample_model_tree('Server', self.db)
        service_1 = Service(name="Example Service 1", server=server, check_name="ICMP IPv4 Check")
        self.db.save(service_1)
        service_2 = Service(name="Example Service 2", server=server, check_name="SSH IPv4 Check")
        self.db.save(service_2)
        assert server.services == [service_1, service_2]
