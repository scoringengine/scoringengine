"""
Comprehensive tests for SLA penalty and dynamic scoring functionality.
"""

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.sla import (
    SLAConfig,
    apply_dynamic_scoring_to_round,
    calculate_round_multiplier,
    calculate_service_adjusted_score,
    calculate_sla_penalty_percent,
    calculate_team_adjusted_score,
    calculate_team_total_penalties,
    get_consecutive_failures,
    get_dynamic_scoring_info,
    get_max_consecutive_failures,
    get_service_sla_status,
    get_sla_config,
    get_team_sla_summary,
)
from tests.scoring_engine.unit_test import UnitTest


class TestSLAConfig(UnitTest):
    """Tests for SLAConfig class."""

    def test_sla_config_loads_defaults(self):
        """Test that SLAConfig loads default values correctly."""
        config = get_sla_config()
        assert config.sla_enabled is False
        assert config.penalty_threshold == 5
        assert config.penalty_percent == 10
        assert config.penalty_max_percent == 50
        assert config.penalty_mode == "additive"
        assert config.allow_negative is False
        assert config.dynamic_enabled is False
        assert config.early_rounds == 10
        assert config.early_multiplier == 2.0
        assert config.late_start_round == 50
        assert config.late_multiplier == 0.5

    def test_sla_config_loads_custom_values(self):
        """Test that SLAConfig loads custom setting values."""
        # Update settings
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        setting = Setting.get_setting("sla_penalty_threshold")
        setting.value = "10"
        db.session.commit()
        Setting.clear_cache("sla_penalty_threshold")

        config = get_sla_config()
        assert config.sla_enabled is True
        assert config.penalty_threshold == 10


class TestConsecutiveFailures(UnitTest):
    """Tests for consecutive failure counting."""

    def setup_service_with_checks(self, results):
        """Helper to create a service with check results."""
        team = Team(name="Test Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Test Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        db.session.add(service)
        db.session.commit()

        # Create checks in order
        for i, result in enumerate(results):
            round_obj = Round(number=i + 1)
            db.session.add(round_obj)
            db.session.commit()

            check = Check(round=round_obj, service=service)
            check.finished(result, "Test", "output", "command")
            db.session.add(check)

        db.session.commit()
        return service

    def test_consecutive_failures_all_pass(self):
        """Test with all passing checks."""
        service = self.setup_service_with_checks([True, True, True, True, True])
        assert get_consecutive_failures(service.id) == 0

    def test_consecutive_failures_all_fail(self):
        """Test with all failing checks."""
        service = self.setup_service_with_checks([False, False, False, False, False])
        assert get_consecutive_failures(service.id) == 5

    def test_consecutive_failures_mixed_ending_in_fail(self):
        """Test with mixed results ending in failures."""
        service = self.setup_service_with_checks([True, True, False, False, False])
        assert get_consecutive_failures(service.id) == 3

    def test_consecutive_failures_mixed_ending_in_pass(self):
        """Test with mixed results ending in pass."""
        service = self.setup_service_with_checks([False, False, False, True])
        assert get_consecutive_failures(service.id) == 0

    def test_consecutive_failures_alternating(self):
        """Test with alternating results."""
        service = self.setup_service_with_checks([True, False, True, False, True])
        assert get_consecutive_failures(service.id) == 0

    def test_max_consecutive_failures(self):
        """Test finding maximum consecutive failure streak."""
        service = self.setup_service_with_checks(
            [True, False, False, False, True, False, False, True]
        )
        assert get_max_consecutive_failures(service.id) == 3

    def test_no_checks(self):
        """Test with no checks."""
        team = Team(name="Test Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Test Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        db.session.add(service)
        db.session.commit()

        assert get_consecutive_failures(service.id) == 0


class TestPenaltyCalculation(UnitTest):
    """Tests for SLA penalty percentage calculations."""

    def test_penalty_below_threshold(self):
        """Test no penalty when below threshold."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False

        assert calculate_sla_penalty_percent(0, config) == 0
        assert calculate_sla_penalty_percent(4, config) == 0

    def test_penalty_at_threshold(self):
        """Test penalty at exactly threshold."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False

        # At threshold (5 failures), penalty should be 10% (1 * penalty_percent)
        assert calculate_sla_penalty_percent(5, config) == 10

    def test_penalty_additive_mode(self):
        """Test additive penalty mode."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False

        # 5 failures: 10%, 6 failures: 20%, 7 failures: 30%, etc.
        assert calculate_sla_penalty_percent(5, config) == 10
        assert calculate_sla_penalty_percent(6, config) == 20
        assert calculate_sla_penalty_percent(7, config) == 30
        # Capped at 50%
        assert calculate_sla_penalty_percent(10, config) == 50
        assert calculate_sla_penalty_percent(20, config) == 50

    def test_penalty_flat_mode(self):
        """Test flat penalty mode."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "flat"
        config.allow_negative = False

        # Flat: 0 at threshold, 10% at 6, 20% at 7, etc.
        assert calculate_sla_penalty_percent(5, config) == 0
        assert calculate_sla_penalty_percent(6, config) == 10
        assert calculate_sla_penalty_percent(7, config) == 20
        # Capped at 50%
        assert calculate_sla_penalty_percent(11, config) == 50

    def test_penalty_exponential_mode(self):
        """Test exponential penalty mode."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 100
        config.penalty_mode = "exponential"
        config.allow_negative = False

        # Exponential: 10%, 20%, 40%, 80%...
        assert calculate_sla_penalty_percent(5, config) == 10
        assert calculate_sla_penalty_percent(6, config) == 20
        assert calculate_sla_penalty_percent(7, config) == 40
        assert calculate_sla_penalty_percent(8, config) == 80
        # Capped at 100%
        assert calculate_sla_penalty_percent(9, config) == 100

    def test_penalty_disabled(self):
        """Test no penalty when SLA is disabled."""
        config = SLAConfig()
        config.sla_enabled = False
        config.penalty_threshold = 5
        config.penalty_percent = 10

        assert calculate_sla_penalty_percent(10, config) == 0

    def test_penalty_allow_negative(self):
        """Test penalty exceeds max when allow_negative is True."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = True

        # With allow_negative, should exceed 50%
        assert calculate_sla_penalty_percent(15, config) > 50


class TestDynamicScoring(UnitTest):
    """Tests for dynamic scoring multipliers."""

    def test_early_phase_multiplier(self):
        """Test multiplier in early phase."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        assert calculate_round_multiplier(1, config) == 2.0
        assert calculate_round_multiplier(5, config) == 2.0
        assert calculate_round_multiplier(10, config) == 2.0

    def test_normal_phase_multiplier(self):
        """Test multiplier in normal phase."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        assert calculate_round_multiplier(11, config) == 1.0
        assert calculate_round_multiplier(25, config) == 1.0
        assert calculate_round_multiplier(49, config) == 1.0

    def test_late_phase_multiplier(self):
        """Test multiplier in late phase."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        assert calculate_round_multiplier(50, config) == 0.5
        assert calculate_round_multiplier(100, config) == 0.5

    def test_dynamic_scoring_disabled(self):
        """Test multiplier when dynamic scoring is disabled."""
        config = SLAConfig()
        config.dynamic_enabled = False
        config.early_rounds = 10
        config.early_multiplier = 2.0

        assert calculate_round_multiplier(1, config) == 1.0
        assert calculate_round_multiplier(100, config) == 1.0

    def test_apply_dynamic_scoring_to_round(self):
        """Test applying multiplier to points."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        assert apply_dynamic_scoring_to_round(5, 100, config) == 200  # Early: 2x
        assert apply_dynamic_scoring_to_round(25, 100, config) == 100  # Normal: 1x
        assert apply_dynamic_scoring_to_round(75, 100, config) == 50  # Late: 0.5x

    def test_dynamic_scoring_info(self):
        """Test get_dynamic_scoring_info returns correct structure."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        info = get_dynamic_scoring_info(config)
        assert info["enabled"] is True
        assert info["early_rounds"] == 10
        assert info["early_multiplier"] == 2.0
        assert info["late_multiplier"] == 0.5
        assert len(info["phases"]) == 3


class TestServiceAndTeamScores(UnitTest):
    """Tests for service and team adjusted scores."""

    def create_team_with_services(self):
        """Helper to create a team with services and checks."""
        team = Team(name="Test Team", color="Blue")
        db.session.add(team)

        # Create two services
        service1 = Service(
            name="Service 1",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        service2 = Service(
            name="Service 2",
            check_name="ICMP",
            team=team,
            host="127.0.0.2",
            port=0,
            points=100,
        )
        db.session.add(service1)
        db.session.add(service2)
        db.session.commit()

        # Create 10 rounds with checks
        for i in range(10):
            round_obj = Round(number=i + 1)
            db.session.add(round_obj)
            db.session.commit()

            # Service 1: all pass
            check1 = Check(round=round_obj, service=service1)
            check1.finished(True, "Pass", "output", "command")
            db.session.add(check1)

            # Service 2: first 3 pass, then all fail (7 consecutive failures)
            check2 = Check(round=round_obj, service=service2)
            check2.finished(i < 3, "Test", "output", "command")
            db.session.add(check2)

        db.session.commit()
        return team, service1, service2

    def test_service_sla_status(self):
        """Test get_service_sla_status returns correct info."""
        team, service1, service2 = self.create_team_with_services()

        # Enable SLA
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        status1 = get_service_sla_status(service1)
        assert status1["consecutive_failures"] == 0
        assert status1["sla_violation"] is False
        assert status1["penalty_percent"] == 0

        status2 = get_service_sla_status(service2)
        assert status2["consecutive_failures"] == 7
        assert status2["sla_violation"] is True
        assert status2["penalty_percent"] > 0

    def test_service_adjusted_score_no_penalty(self):
        """Test adjusted score without penalty."""
        team, service1, service2 = self.create_team_with_services()

        # SLA disabled by default
        assert calculate_service_adjusted_score(service1) == service1.score_earned

    def test_service_adjusted_score_with_penalty(self):
        """Test adjusted score with penalty applied."""
        team, service1, service2 = self.create_team_with_services()

        # Enable SLA
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        adjusted = calculate_service_adjusted_score(service2)
        base = service2.score_earned
        assert adjusted < base  # Should be lower due to penalty

    def test_team_total_penalties(self):
        """Test calculating total team penalties."""
        team, service1, service2 = self.create_team_with_services()

        # Enable SLA
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        total = calculate_team_total_penalties(team)
        # Only service2 has violations, so penalty should be > 0
        assert total > 0

    def test_team_adjusted_score(self):
        """Test team adjusted score."""
        team, service1, service2 = self.create_team_with_services()

        # Enable SLA
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        adjusted = calculate_team_adjusted_score(team)
        base = team.current_score
        assert adjusted <= base  # Should be lower or equal due to penalties

    def test_team_sla_summary(self):
        """Test get_team_sla_summary returns correct structure."""
        team, service1, service2 = self.create_team_with_services()

        summary = get_team_sla_summary(team)
        assert summary["team_name"] == "Test Team"
        assert "base_score" in summary
        assert "total_penalties" in summary
        assert "adjusted_score" in summary
        assert "services" in summary
        assert len(summary["services"]) == 2


class TestServiceModelSLAProperties(UnitTest):
    """Tests for SLA properties added to Service model."""

    def setup_service(self, results):
        """Helper to create a service with check results."""
        team = Team(name="Test Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Test Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        db.session.add(service)
        db.session.commit()

        for i, result in enumerate(results):
            round_obj = Round(number=i + 1)
            db.session.add(round_obj)
            db.session.commit()

            check = Check(round=round_obj, service=service)
            check.finished(result, "Test", "output", "command")
            db.session.add(check)

        db.session.commit()
        return service

    def test_service_consecutive_failures_property(self):
        """Test Service.consecutive_failures property."""
        service = self.setup_service([True, True, False, False, False])
        assert service.consecutive_failures == 3

    def test_service_sla_penalty_percent_property(self):
        """Test Service.sla_penalty_percent property."""
        service = self.setup_service([False] * 10)

        # Enable SLA with threshold 5
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        assert service.sla_penalty_percent > 0

    def test_service_adjusted_score_property(self):
        """Test Service.adjusted_score property."""
        service = self.setup_service([True] * 10)

        # All passing, no penalty
        assert service.adjusted_score == service.score_earned

    def test_service_sla_status_property(self):
        """Test Service.sla_status property."""
        service = self.setup_service([True, True, True])
        status = service.sla_status
        assert "consecutive_failures" in status
        assert "sla_violation" in status


class TestTeamModelSLAProperties(UnitTest):
    """Tests for SLA properties added to Team model."""

    def create_team_with_checks(self):
        """Helper to create a team with services and checks."""
        team = Team(name="Test Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Test Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        db.session.add(service)
        db.session.commit()

        for i in range(10):
            round_obj = Round(number=i + 1)
            db.session.add(round_obj)
            db.session.commit()

            check = Check(round=round_obj, service=service)
            check.finished(i < 3, "Test", "output", "command")  # 3 pass, 7 fail
            db.session.add(check)

        db.session.commit()
        return team

    def test_team_total_sla_penalties_property(self):
        """Test Team.total_sla_penalties property."""
        team = self.create_team_with_checks()

        # Enable SLA
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        assert team.total_sla_penalties > 0

    def test_team_adjusted_score_property(self):
        """Test Team.adjusted_score property."""
        team = self.create_team_with_checks()

        # Enable SLA
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        assert team.adjusted_score <= team.current_score

    def test_team_sla_summary_property(self):
        """Test Team.sla_summary property."""
        team = self.create_team_with_checks()
        summary = team.sla_summary
        assert "team_name" in summary
        assert "services" in summary

    def test_team_services_with_sla_violations_property(self):
        """Test Team.services_with_sla_violations property."""
        team = self.create_team_with_checks()

        # Enable SLA with threshold 5
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        # 7 consecutive failures > threshold 5
        assert team.services_with_sla_violations >= 1
