import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.account import Account

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest


class TestAccount(UnitTest):

    def test_init_account(self):
        account = Account(username="testname", password="testpass")
        assert account.id is None
        assert account.username == "testname"
        assert account.password == "testpass"
        assert account.service is None
        assert account.service_id is None

    def test_basic_property(self):
        service = generate_sample_model_tree('Service', self.db)
        account = Account(username="testname", password="testpass", service=service)
        self.db.save(account)
        assert account.id is not None
        assert account.service == service
        assert account.service_id == service.id
