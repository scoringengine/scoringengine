import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.username_password_check import UsernamePasswordCheck
from scoring_engine.models.service import Service
from scoring_engine.models.property import Property

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from unit_test import UnitTest


class TestBasicCheck(UnitTest):

    def setup(self):
        super(TestBasicCheck, self).setup()
        service = Service(name="Example Service", check_name="ICMP IPv4 Check")
        property1 = Property(name="IP Address", value="127.0.0.1", service=service)
        self.db.save(service)
        self.db.save(property1)
        self.check = UsernamePasswordCheck(service)

    def test_init(self):
        assert self.check.get_ip_address() == "127.0.0.1"

    def test_with_creds(self):
        self.check.set_credentials('testuser', 'testpass')
        assert self.check.username == 'testuser'
        assert self.check.password == 'testpass'
