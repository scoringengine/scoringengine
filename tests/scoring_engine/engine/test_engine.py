import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.engine import Engine

from scoring_engine.models.team import Team
from scoring_engine.models.service import Service
from scoring_engine.models.property import Property
from scoring_engine.models.check import Check

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from unit_test import UnitTest


class TestEngine(UnitTest):

    def test_init(self):
        engine = Engine()
        from ipv4.ssh import SSHCheck
        from ipv4.icmp import ICMPCheck
        expected_checks = [ICMPCheck, SSHCheck]
        assert engine.checks == expected_checks

    def test_current_round_init(self):
        engine = Engine(current_round=100)
        assert engine.current_round == 100

    def test_total_rounds_init(self):
        engine = Engine(total_rounds=100)
        assert engine.total_rounds == 100

    def test_shutdown(self):
        engine = Engine()
        assert engine.last_round is False
        engine.shutdown()
        assert engine.last_round is True

    def test_run_one_round(self):
        engine = Engine(current_round=1, total_rounds=1)
        assert engine.rounds_run == 0
        assert engine.current_round == 1
        engine.run()
        assert engine.rounds_run == 1
        assert engine.current_round == 2

    def test_run_ten_rounds(self):
        engine = Engine(total_rounds=10)
        assert engine.current_round == 1
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 10
        assert engine.current_round == 11

    def test_run_hundred_rounds(self):
        engine = Engine(current_round=50, total_rounds=100)
        assert engine.current_round == 50
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 100
        assert engine.current_round == 150

    def test_check_name_to_obj_positive(self):
        engine = Engine()
        check_obj = engine.check_name_to_obj("ICMP IPv4 Check")
        from ipv4.icmp import ICMPCheck
        check_obj == ICMPCheck

    def test_check_name_to_obj_negative(self):
        engine = Engine()
        check_obj = engine.check_name_to_obj("Garbage Check")
        assert check_obj is None

    def test_with_one_team(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        service = Service(name="Example Service 2", team=team, check_name="ICMP IPv4 Check")
        property1 = Property(name="IP Address", value="127.0.0.1", service=service)
        self.db.save(service)
        self.db.save(property1)

        engine = Engine(current_round=50, total_rounds=100)
        engine.run()

    def test_engine_populates_worker_queue_one_service(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        service = Service(name="Example Service 2", team=team, check_name="ICMP IPv4 Check")
        property1 = Property(name="IP Address", value="127.0.0.1", service=service)
        self.db.save(service)
        self.db.save(property1)

        engine = Engine(total_rounds=1)
        assert engine.worker_queue.size() == 0
        engine.run()
        assert engine.worker_queue.size() == 1

    def test_engine_populates_worker_queue_one_team_five_services(self):
        team = Team(name="Team1", color="Blue")
        self.db.save(team)
        for num in range(1, 6):
            service = Service(name="Example Service " + str(num), team=team, check_name="ICMP IPv4 Check")
            property1 = Property(name="IP Address", value="127.0.0.1", service=service)
            self.db.save(service)
            self.db.save(property1)

        engine = Engine(total_rounds=1)
        assert engine.worker_queue.size() == 0
        engine.run()
        assert engine.worker_queue.size() == 5

    def test_engine_populates_worker_queue_five_teams_one_service(self):
        for num in range(1, 6):
            team = Team(name="Team" + str(num), color="Blue")
            self.db.save(team)
            service = Service(name="Example Service " + str(num), team=team, check_name="ICMP IPv4 Check")
            property1 = Property(name="IP Address", value="127.0.0.1", service=service)
            self.db.save(service)
            self.db.save(property1)

        engine = Engine(total_rounds=1)
        assert engine.worker_queue.size() == 0
        engine.run()
        assert engine.worker_queue.size() == 5

    def test_engine_populates_worker_queue_five_teams_five_services(self):
        for num in range(1, 6):
            team = Team(name="Team" + str(num), color="Blue")
            self.db.save(team)
            for service_num in range(1, 6):
                service = Service(name="Example Service " + str(service_num), team=team, check_name="ICMP IPv4 Check")
                property1 = Property(name="IP Address", value="127.0.0.1", service=service)
                self.db.save(service)
                self.db.save(property1)

        engine = Engine(total_rounds=1)
        assert engine.worker_queue.size() == 0
        engine.run()
        assert engine.worker_queue.size() == 25