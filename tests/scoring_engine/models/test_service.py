import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.team import Team
from models.server import Server
from models.service import Service
from models.check import Check
from models.property import Property
from db import DB


class TestService(object):
    def setup(self):
        self.db = DB()
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()

    def test_init_service(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check")
        assert service.id is None
        assert service.name == "Example Service"
        assert service.server is None
        assert service.server_id is None
        assert service.check_name == "ICMP IPv4 Check"

    def test_basic_service(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        server = Server(name="Example Server", team=team)
        self.db.save(server)
        service = Service(name="Example Service", server=server, check_name="ICMP IPv4 Check")
        self.db.save(service)
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.server == server
        assert service.server_id == 1
        assert service.check_name == "ICMP IPv4 Check"

    def test_checks(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        server = Server(name="Example Server", team=team)
        self.db.save(server)
        service = Service(name="Example Service 2", server=server, check_name="ICMP IPv4 Check")
        self.db.save(service)
        check_1 = Check(round_num=1, service=service)
        self.db.save(check_1)
        check_2 = Check(round_num=2, service=service)
        self.db.save(check_2)
        check_3 = Check(round_num=3, service=service)
        self.db.save(check_3)

        assert service.checks == [check_1, check_2, check_3]

    def test_properties(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        server = Server(name="Example Server", team=team)
        self.db.save(server)
        service = Service(name="Example Service 2", server=server, check_name="ICMP IPv4 Check")
        self.db.save(service)
        property_1 = Property(name="testname", value="testvalue", service=service)
        self.db.save(property_1)
        property_2 = Property(name="testname", value="testvalue", service=service)
        self.db.save(property_2)
        property_3 = Property(name="testname", value="testvalue", service=service)
        self.db.save(property_3)

        assert service.properties == [property_1, property_2, property_3]

