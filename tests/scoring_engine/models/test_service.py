import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.service import Service
from models.check import Check
from models.property import Property
from db import DB

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree


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
        server = generate_sample_model_tree('Server', self.db)
        service = Service(name="Example Service", server=server, check_name="ICMP IPv4 Check")
        self.db.save(service)
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.server == server
        assert service.server_id == server.id
        assert service.check_name == "ICMP IPv4 Check"

    def test_checks(self):
        service = generate_sample_model_tree('Service', self.db)
        round_obj = generate_sample_model_tree('Round', self.db)
        check_1 = Check(round=round_obj, service=service)
        self.db.save(check_1)
        check_2 = Check(round=round_obj, service=service)
        self.db.save(check_2)
        check_3 = Check(round=round_obj, service=service)
        self.db.save(check_3)
        assert service.checks == [check_1, check_2, check_3]

    def test_properties(self):
        service = generate_sample_model_tree('Service', self.db)
        property_1 = Property(name="ip", value="127.0.0.1", service=service)
        self.db.save(property_1)
        property_2 = Property(name="username", value="testuser", service=service)
        self.db.save(property_2)
        property_3 = Property(name="password", value="testpass", service=service)
        self.db.save(property_3)
        assert service.properties == [property_1, property_2, property_3]
