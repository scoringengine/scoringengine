from scoring_engine.db import db
from scoring_engine.models.account import Account
from tests.scoring_engine.helpers import generate_sample_model_tree


class TestAccount:

    def test_init_account(self):
        account = Account(username="testname", password="testpass")
        assert account.id is None
        assert account.username == "testname"
        assert account.password == "testpass"
        assert account.service is None
        assert account.service_id is None

    def test_basic_property(self):
        service = generate_sample_model_tree("Service", db.session)
        account = Account(username="testname", password="testpass", service=service)
        db.session.add(account)
        db.session.commit()
        assert account.id is not None
        assert account.service == service
        assert account.service_id == service.id
