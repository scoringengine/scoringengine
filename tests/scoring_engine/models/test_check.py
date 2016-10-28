import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.team import Team
from models.server import Server
from models.service import Service
from models.check import Check
from db import DB

from helpers import generate_sample_model_tree


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
        service = generate_sample_model_tree('Service', self.db)
        check = Check(round_num=1, service=service)
        self.db.save(check)
        assert check.id is not None
        assert check.service == service
        assert check.service_id == service.id
