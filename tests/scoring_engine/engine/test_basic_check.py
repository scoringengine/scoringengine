import pytest

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.basic_check import BasicCheck
from scoring_engine.models.service import Service
from scoring_engine.models.property import Property

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from unit_test import UnitTest


class TestBasicCheck(UnitTest):

    def test_init(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check")
        check = BasicCheck(service)
        assert check.service == service

    def test_properties(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check")
        property1 = Property(name="IP Address", value="127.0.0.1", service=service)
        property2 = Property(name="Path", value="/index.html", service=service)
        self.db.save(service)
        self.db.save(property1)
        self.db.save(property2)
        check = BasicCheck(service)
        assert check.properties() == [property1, property2]

    def test_get_ip_address_good(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check")
        property1 = Property(name="IP Address", value="127.0.0.1", service=service)
        self.db.save(service)
        self.db.save(property1)
        check = BasicCheck(service)
        assert check.get_ip_address() == '127.0.0.1'

    def test_get_ip_address_bad(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check")
        property1 = Property(name="Path", value="/index.html", service=service)
        self.db.save(service)
        self.db.save(property1)
        check = BasicCheck(service)
        with pytest.raises(LookupError):
            check.get_ip_address()
