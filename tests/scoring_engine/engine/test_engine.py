from scoring_engine.engine.engine import Engine

from scoring_engine.models.team import Team
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment

from tests.scoring_engine.unit_test import UnitTest


class TestEngine(UnitTest):

    def test_init(self):
        engine = Engine()
        from scoring_engine.engine.checks.icmp import ICMPCheck
        from scoring_engine.engine.checks.ssh import SSHCheck
        from scoring_engine.engine.checks.dns import DNSCheck
        expected_checks = [ICMPCheck, SSHCheck, DNSCheck]
        assert set(engine.checks) == set(expected_checks)

    def test_total_rounds_init(self):
        engine = Engine(total_rounds=100)
        assert engine.total_rounds == 100

    def test_custom_sleep_timers(self):
        engine = Engine(round_time_sleep=60, worker_wait_time=20)
        assert engine.round_time_sleep == 60
        assert engine.worker_wait_time == 20

    def test_shutdown(self):
        engine = Engine()
        assert engine.last_round is False
        engine.shutdown()
        assert engine.last_round is True

    def test_run_one_round(self):
        engine = Engine(total_rounds=1, round_time_sleep=1, worker_wait_time=1)
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 1
        assert engine.current_round == 1

    def test_run_ten_rounds(self):
        engine = Engine(total_rounds=10, round_time_sleep=0, worker_wait_time=0)
        assert engine.current_round == 0
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 10
        assert engine.current_round == 10

    def test_run_hundred_rounds(self):
        engine = Engine(total_rounds=100, round_time_sleep=0, worker_wait_time=0)
        assert engine.current_round == 0
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 100
        assert engine.current_round == 100

    def test_check_name_to_obj_positive(self):
        engine = Engine()
        check_obj = engine.check_name_to_obj("ICMP IPv4 Check")
        from scoring_engine.engine.checks.icmp import ICMPCheck
        check_obj == ICMPCheck

    def test_check_name_to_obj_negative(self):
        engine = Engine()
        check_obj = engine.check_name_to_obj("Garbage Check")
        assert check_obj is None

    # todo figure out how to test the remaining functionality of engine
    # where we're waiting for the worker queues to finish and everything
    # so we can uncomment out the following lines
    # def test_with_one_team(self):
    #     team = Team(name="Team1", color="Blue")
    #     self.db.save(team)
    #     service = Service(name="Example Service 2", team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
    #     self.db.save(service)
    #     environment = Environment(matching_regex='*', service=service)
    #     self.db.save(environment)

    #     engine = Engine(total_rounds=100, round_time_sleep=0, worker_wait_time=0)
    #     engine.run()

    # def test_engine_populates_worker_queue_one_service(self):
    #     team = Team(name="Team1", color="Blue")
    #     self.db.save(team)
    #     service = Service(name="Example Service 2", team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
    #     self.db.save(service)

    #     engine = Engine(total_rounds=1)
    #     assert engine.worker_queue.size() == 0
    #     engine.run()
    #     assert engine.worker_queue.size() == 1

    # def test_engine_populates_worker_queue_one_team_five_services(self):
    #     team = Team(name="Team1", color="Blue")
    #     self.db.save(team)
    #     for num in range(1, 6):
    #         service = Service(name="Example Service" + str(num), team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
    #         self.db.save(service)

    #     engine = Engine(total_rounds=1)
    #     assert engine.worker_queue.size() == 0
    #     engine.run()
    #     assert engine.worker_queue.size() == 5

    # def test_engine_populates_worker_queue_five_teams_one_service(self):
    #     for num in range(1, 6):
    #         team = Team(name="Team" + str(num), color="Blue")
    #         self.db.save(team)
    #         service = Service(name="Example Service" + str(num), team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
    #         self.db.save(service)

    #     engine = Engine(total_rounds=1)
    #     assert engine.worker_queue.size() == 0
    #     engine.run()
    #     assert engine.worker_queue.size() == 5

    # def test_engine_populates_worker_queue_five_teams_five_services(self):
    #     for num in range(1, 6):
    #         team = Team(name="Team" + str(num), color="Blue")
    #         self.db.save(team)
    #         for service_num in range(1, 6):
    #             service = Service(name="Example Service" + str(service_num), team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
    #             self.db.save(service)

    #     engine = Engine(total_rounds=1)
    #     assert engine.worker_queue.size() == 0
    #     engine.run()
    #     assert engine.worker_queue.size() == 25
