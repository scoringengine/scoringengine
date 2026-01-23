"""
Comprehensive tests for SLA penalty and dynamic scoring functionality.
"""

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.sla import (SLAConfig, apply_dynamic_scoring_to_round,
                                calculate_round_multiplier,
                                calculate_service_adjusted_score,
                                calculate_sla_penalty_percent,
                                calculate_team_adjusted_score,
                                calculate_team_base_score_with_dynamic,
                                calculate_team_total_penalties,
                                get_consecutive_failures,
                                get_dynamic_scoring_info,
                                get_max_consecutive_failures,
                                get_service_sla_status, get_sla_config,
                                get_team_sla_summary)
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

    def _get_enabled_sla_config(self):
        """Create an SLA config with SLA enabled for testing."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False
        return config

    def test_service_sla_status(self):
        """Test get_service_sla_status returns correct info."""
        team, service1, service2 = self.create_team_with_services()

        # Use explicit config with SLA enabled
        config = self._get_enabled_sla_config()

        status1 = get_service_sla_status(service1, config)
        assert status1["consecutive_failures"] == 0
        assert status1["sla_violation"] is False
        assert status1["penalty_percent"] == 0

        status2 = get_service_sla_status(service2, config)
        assert status2["consecutive_failures"] == 7
        assert status2["sla_violation"] is True
        assert status2["penalty_percent"] > 0

    def test_service_adjusted_score_no_penalty(self):
        """Test adjusted score without penalty."""
        team, service1, service2 = self.create_team_with_services()

        # SLA disabled config
        config = SLAConfig()
        config.sla_enabled = False
        assert (
            calculate_service_adjusted_score(service1, config) == service1.score_earned
        )

    def test_service_adjusted_score_with_penalty(self):
        """Test adjusted score with penalty applied."""
        team, service1, service2 = self.create_team_with_services()

        # Use explicit config with SLA enabled
        config = self._get_enabled_sla_config()

        adjusted = calculate_service_adjusted_score(service2, config)
        base = service2.score_earned
        assert adjusted < base  # Should be lower due to penalty

    def test_team_total_penalties(self):
        """Test calculating total team penalties."""
        team, service1, service2 = self.create_team_with_services()

        # Use explicit config with SLA enabled
        config = self._get_enabled_sla_config()

        total = calculate_team_total_penalties(team, config)
        # Only service2 has violations, so penalty should be > 0
        assert total > 0

    def test_team_adjusted_score(self):
        """Test team adjusted score."""
        team, service1, service2 = self.create_team_with_services()

        # Use explicit config with SLA enabled
        config = self._get_enabled_sla_config()

        adjusted = calculate_team_adjusted_score(team, config)
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
        """Test Service.sla_penalty_percent property with explicit config."""
        service = self.setup_service([False] * 10)

        # Clear all setting caches and enable SLA
        Setting.clear_cache()
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache()

        # With 10 consecutive failures and threshold 5, penalty should be > 0
        assert service.sla_penalty_percent > 0

    def test_service_adjusted_score_property(self):
        """Test Service.adjusted_score property."""
        service = self.setup_service([True] * 10)

        # All passing, no penalty (SLA disabled by default)
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

        # Clear all caches and enable SLA
        Setting.clear_cache()
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache()

        assert team.total_sla_penalties > 0

    def test_team_adjusted_score_property(self):
        """Test Team.adjusted_score property."""
        team = self.create_team_with_checks()

        # Clear all caches and enable SLA
        Setting.clear_cache()
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache()

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

        # Clear all caches and enable SLA with threshold 5
        Setting.clear_cache()
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache()

        # 7 consecutive failures > threshold 5
        assert team.services_with_sla_violations >= 1


class TestPenaltyEdgeCases(UnitTest):
    """Tests for edge cases in penalty calculations."""

    def test_penalty_next_check_reduction_mode(self):
        """Test next_check_reduction penalty mode."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "next_check_reduction"
        config.allow_negative = False

        # Similar to additive but capped
        assert calculate_sla_penalty_percent(5, config) == 10
        assert calculate_sla_penalty_percent(6, config) == 20
        assert calculate_sla_penalty_percent(10, config) == 50  # Capped

    def test_penalty_threshold_of_one(self):
        """Test with threshold of 1 (immediate penalty)."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 1
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False

        assert calculate_sla_penalty_percent(0, config) == 0
        assert calculate_sla_penalty_percent(1, config) == 10
        assert calculate_sla_penalty_percent(2, config) == 20

    def test_penalty_zero_percent(self):
        """Test with 0% penalty (essentially disabled)."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 0
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False

        assert calculate_sla_penalty_percent(10, config) == 0

    def test_penalty_100_percent_max(self):
        """Test with 100% max penalty."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 50
        config.penalty_max_percent = 100
        config.penalty_mode = "additive"
        config.allow_negative = False

        assert calculate_sla_penalty_percent(5, config) == 50
        assert calculate_sla_penalty_percent(6, config) == 100
        assert calculate_sla_penalty_percent(7, config) == 100  # Capped

    def test_unknown_penalty_mode_defaults_to_additive(self):
        """Test that unknown penalty mode defaults to additive."""
        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "unknown_mode"
        config.allow_negative = False

        # Should behave like additive
        assert calculate_sla_penalty_percent(5, config) == 10
        assert calculate_sla_penalty_percent(6, config) == 20


class TestNegativeScoreScenarios(UnitTest):
    """Tests for negative score scenarios."""

    def create_team_with_failing_service(self):
        """Create a team with a service that has many failures."""
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

        # Create 20 rounds - first 5 pass, then 15 fail
        for i in range(20):
            round_obj = Round(number=i + 1)
            db.session.add(round_obj)
            db.session.commit()

            check = Check(round=round_obj, service=service)
            check.finished(i < 5, "Test", "output", "command")
            db.session.add(check)

        db.session.commit()
        return team, service

    def test_adjusted_score_cannot_go_negative_by_default(self):
        """Test that adjusted score is capped at 0 when allow_negative is False."""
        team, service = self.create_team_with_failing_service()

        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 50
        config.penalty_max_percent = 200  # Allow high penalty
        config.penalty_mode = "additive"
        config.allow_negative = False

        adjusted = calculate_service_adjusted_score(service, config)
        assert adjusted >= 0

    def test_adjusted_score_can_go_negative_when_allowed(self):
        """Test that adjusted score can go negative when allow_negative is True."""
        team, service = self.create_team_with_failing_service()

        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 50
        config.penalty_max_percent = 500  # Very high penalty
        config.penalty_mode = "additive"
        config.allow_negative = True

        # With 15 consecutive failures after threshold 5, penalty = 550%
        # With allow_negative=True, penalty can exceed score
        penalty_percent = calculate_sla_penalty_percent(15, config)
        assert penalty_percent > 100  # Verify penalty is > 100%

        # Calculate adjusted score - it should be negative
        adjusted = calculate_service_adjusted_score(service, config)
        assert adjusted < 0  # Score goes negative when penalty exceeds earned score


class TestDynamicScoringEdgeCases(UnitTest):
    """Tests for dynamic scoring edge cases."""

    def test_round_zero(self):
        """Test multiplier at round 0."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        # Round 0 should use early multiplier
        assert calculate_round_multiplier(0, config) == 2.0

    def test_boundary_between_early_and_normal(self):
        """Test exact boundary between early and normal phase."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        assert calculate_round_multiplier(10, config) == 2.0  # Last early round
        assert calculate_round_multiplier(11, config) == 1.0  # First normal round

    def test_boundary_between_normal_and_late(self):
        """Test exact boundary between normal and late phase."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        assert calculate_round_multiplier(49, config) == 1.0  # Last normal round
        assert calculate_round_multiplier(50, config) == 0.5  # First late round

    def test_early_equals_late_start(self):
        """Test when early_rounds equals late_start_round (no normal phase)."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 10  # Same as early_rounds
        config.late_multiplier = 0.5

        assert calculate_round_multiplier(10, config) == 2.0  # Early phase
        # Note: There's no normal phase, goes directly from early to late

    def test_very_high_round_number(self):
        """Test with very high round number."""
        config = SLAConfig()
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5

        assert calculate_round_multiplier(10000, config) == 0.5


class TestMultipleTeams(UnitTest):
    """Tests for multiple teams scenarios."""

    def create_multiple_teams(self):
        """Create multiple teams with different service statuses."""
        teams = []
        for i in range(3):
            team = Team(name=f"Team {i+1}", color="Blue")
            db.session.add(team)

            service = Service(
                name=f"Service {i+1}",
                check_name="ICMP",
                team=team,
                host=f"192.168.1.{i+1}",
                port=0,
                points=100,
            )
            db.session.add(service)
            teams.append(team)

        db.session.commit()

        # Create rounds with different failure patterns per team
        for round_num in range(10):
            round_obj = Round(number=round_num + 1)
            db.session.add(round_obj)
            db.session.commit()

            for i, team in enumerate(teams):
                service = team.services[0]
                check = Check(round=round_obj, service=service)
                # Team 1: all pass (10 passes)
                # Team 2: first 5 pass, then 5 failures (5 consecutive failures)
                # Team 3: first 2 pass, then 8 failures (8 consecutive failures)
                if i == 0:
                    result = True
                elif i == 1:
                    result = round_num < 5  # rounds 0-4 pass, 5-9 fail
                else:
                    result = round_num < 2  # rounds 0-1 pass, 2-9 fail (8 failures)
                check.finished(result, "Test", "output", "command")
                db.session.add(check)

        db.session.commit()
        return teams

    def test_different_penalties_per_team(self):
        """Test that different teams get different penalties based on their failures."""
        teams = self.create_multiple_teams()

        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False

        penalties = [calculate_team_total_penalties(team, config) for team in teams]

        # Team 1 (all pass): no penalty
        assert penalties[0] == 0

        # Team 2 (5 consecutive failures): at threshold, some penalty
        assert penalties[1] > 0

        # Team 3 (8 consecutive failures): more failures over threshold = higher penalty %
        # And Team 3 earned 200 points (2 passes), Team 2 earned 500 points (5 passes)
        # Team 2: 500 * 10% = 50 penalty (5 failures, 0 over threshold, (0+1)*10=10%)
        # Team 3: 200 * 40% = 80 penalty (8 failures, 3 over threshold, (3+1)*10=40%)
        assert penalties[2] > penalties[1]

    def test_team_ranking_with_penalties(self):
        """Test that penalties affect relative team scores."""
        teams = self.create_multiple_teams()

        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False

        adjusted_scores = [
            calculate_team_adjusted_score(team, config) for team in teams
        ]

        # Team 1 should have highest score (no penalties, all passes)
        # Team 3 should have lowest (most penalties, no passes)
        assert adjusted_scores[0] > adjusted_scores[1]
        assert adjusted_scores[1] > adjusted_scores[2]


class TestSLAStatusFields(UnitTest):
    """Tests for SLA status field completeness."""

    def create_service_with_violations(self):
        """Create a service with SLA violations."""
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

        # Create 10 failing checks
        for i in range(10):
            round_obj = Round(number=i + 1)
            db.session.add(round_obj)
            db.session.commit()

            check = Check(round=round_obj, service=service)
            check.finished(False, "Failure", "output", "command")
            db.session.add(check)

        db.session.commit()
        return team, service

    def test_service_sla_status_all_fields(self):
        """Test that get_service_sla_status returns all expected fields."""
        team, service = self.create_service_with_violations()

        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False

        status = get_service_sla_status(service, config)

        # Verify all expected fields exist
        assert "service_id" in status
        assert "service_name" in status
        assert "consecutive_failures" in status
        assert "penalty_threshold" in status
        assert "penalty_percent" in status
        assert "penalty_points" in status
        assert "base_score" in status
        assert "adjusted_score" in status
        assert "sla_violation" in status

        # Verify field values
        assert status["service_id"] == service.id
        assert status["service_name"] == "Test Service"
        assert status["consecutive_failures"] == 10
        assert status["penalty_threshold"] == 5
        assert status["sla_violation"] is True

    def test_team_sla_summary_all_fields(self):
        """Test that get_team_sla_summary returns all expected fields."""
        team, service = self.create_service_with_violations()

        config = SLAConfig()
        config.sla_enabled = True
        config.penalty_threshold = 5

        summary = get_team_sla_summary(team, config)

        # Verify all expected fields exist
        assert "team_id" in summary
        assert "team_name" in summary
        assert "sla_enabled" in summary
        assert "base_score" in summary
        assert "total_penalties" in summary
        assert "adjusted_score" in summary
        assert "services_with_violations" in summary
        assert "total_services" in summary
        assert "services" in summary

        # Verify field values
        assert summary["team_id"] == team.id
        assert summary["team_name"] == "Test Team"
        assert summary["services_with_violations"] == 1
        assert summary["total_services"] == 1
        assert len(summary["services"]) == 1


class TestCombinedDynamicScoringAndPenalties(UnitTest):
    """Tests for combined dynamic scoring multipliers AND SLA penalties.

    These tests verify the interaction between both features when enabled simultaneously.
    """

    def _create_combined_config(self):
        """Create an SLAConfig with both dynamic scoring and SLA penalties enabled."""
        config = SLAConfig()
        # SLA penalty settings
        config.sla_enabled = True
        config.penalty_threshold = 5
        config.penalty_percent = 10
        config.penalty_max_percent = 50
        config.penalty_mode = "additive"
        config.allow_negative = False
        # Dynamic scoring settings
        config.dynamic_enabled = True
        config.early_rounds = 10
        config.early_multiplier = 2.0
        config.late_start_round = 50
        config.late_multiplier = 0.5
        return config

    def _create_team_with_rounds(self, check_results, points=100):
        """
        Helper to create a team with a service and checks across rounds.

        Args:
            check_results: List of booleans indicating pass/fail for each round
            points: Points per service check

        Returns:
            Tuple of (team, service)
        """
        team = Team(name="Test Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Test Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=points,
        )
        db.session.add(service)
        db.session.commit()

        for i, result in enumerate(check_results):
            round_obj = Round(number=i + 1)
            db.session.add(round_obj)
            db.session.commit()

            check = Check(round=round_obj, service=service)
            check.finished(result, "Test", "output", "command")
            db.session.add(check)

        db.session.commit()
        return team, service

    def test_early_rounds_with_sla_penalty(self):
        """Test that 2x early multiplier applies before SLA penalty is deducted.

        Scenario: Early rounds (2x multiplier) + SLA penalty
        - 15 rounds, all in early phase (rounds 1-10 early, 11-15 would be normal)
        - We'll use first 10 rounds: 5 pass, then 5 fail (5 consecutive failures = at threshold)
        - Expected: Base score with 2x multiplier, then penalty applied to that dynamic score
        """
        # Create checks: 5 pass + 5 fail = 10 rounds (all early phase)
        check_results = [True] * 5 + [False] * 5
        team, service = self._create_team_with_rounds(check_results, points=100)

        config = self._create_combined_config()

        # Calculate expected score:
        # Early rounds (1-10) have 2x multiplier
        # 5 passing checks * 100 points * 2.0 = 1000 base score with dynamic
        # 5 consecutive failures at threshold = 10% penalty (1 * 10%)
        # Penalty = 1000 * 10% = 100 points (penalty based on dynamic score)
        # Adjusted = 1000 - 100 = 900

        base_score = calculate_team_base_score_with_dynamic(team, config)
        assert base_score == 1000, f"Expected 1000 base with 2x early multiplier, got {base_score}"

        penalties = calculate_team_total_penalties(team, config)
        assert penalties == 100, f"Expected 100 penalty (10% of 1000 dynamic), got {penalties}"

        adjusted_score = calculate_team_adjusted_score(team, config)
        assert adjusted_score == 900, f"Expected 900 adjusted score, got {adjusted_score}"

    def test_late_rounds_with_sla_penalty(self):
        """Test that 0.5x late multiplier applies with SLA penalty.

        Scenario: Late rounds (0.5x multiplier) + SLA penalty
        - Rounds 50-60 (all late phase with 0.5x)
        - 4 pass, then 7 consecutive failures (exceeds threshold by 2)
        """
        team = Team(name="Late Test Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Late Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        db.session.add(service)
        db.session.commit()

        # Create rounds 50-60 (all in late phase)
        check_results = [True] * 4 + [False] * 7  # 4 pass, 7 fail
        for i, result in enumerate(check_results):
            round_obj = Round(number=50 + i)  # Rounds 50, 51, 52...
            db.session.add(round_obj)
            db.session.commit()

            check = Check(round=round_obj, service=service)
            check.finished(result, "Test", "output", "command")
            db.session.add(check)

        db.session.commit()

        config = self._create_combined_config()

        # Calculate expected:
        # Late rounds (50+) have 0.5x multiplier
        # Dynamic base: 4 passing checks * 100 points * 0.5 = 200
        # 7 consecutive failures, threshold 5 = 2 over, penalty = (2+1)*10% = 30%
        # Penalty = 200 * 30% = 60 points (penalty based on dynamic score)
        # Adjusted = 200 - 60 = 140

        base_score = calculate_team_base_score_with_dynamic(team, config)
        assert base_score == 200, f"Expected 200 base with 0.5x late multiplier, got {base_score}"

        penalties = calculate_team_total_penalties(team, config)
        assert penalties == 60, f"Expected 60 penalty (30% of 200 dynamic), got {penalties}"

        adjusted_score = calculate_team_adjusted_score(team, config)
        assert adjusted_score == 140, f"Expected 140 adjusted score, got {adjusted_score}"

    def test_mixed_phases_with_sla_penalty(self):
        """Test scoring across all three phases with SLA penalties.

        Scenario: Checks spanning early, normal, and late phases with SLA violation
        - Rounds 1-10: early phase (2x) - 10 pass
        - Rounds 11-49: normal phase (1x) - 10 pass (rounds 11-20)
        - Rounds 50-60: late phase (0.5x) - 3 pass, then 8 fail (consecutive)
        """
        team = Team(name="Mixed Phase Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Mixed Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        db.session.add(service)
        db.session.commit()

        # Early phase: rounds 1-10, all pass
        for i in range(1, 11):
            round_obj = Round(number=i)
            db.session.add(round_obj)
            db.session.commit()
            check = Check(round=round_obj, service=service)
            check.finished(True, "Pass", "output", "command")
            db.session.add(check)

        # Normal phase: rounds 11-20, all pass
        for i in range(11, 21):
            round_obj = Round(number=i)
            db.session.add(round_obj)
            db.session.commit()
            check = Check(round=round_obj, service=service)
            check.finished(True, "Pass", "output", "command")
            db.session.add(check)

        # Late phase: rounds 50-60, 3 pass then 8 fail
        for i in range(50, 61):
            round_obj = Round(number=i)
            db.session.add(round_obj)
            db.session.commit()
            result = i < 53  # rounds 50,51,52 pass; 53-60 fail
            check = Check(round=round_obj, service=service)
            check.finished(result, "Test", "output", "command")
            db.session.add(check)

        db.session.commit()

        config = self._create_combined_config()

        # Calculate expected:
        # Dynamic scores:
        # Early (rounds 1-10): 10 * 100 * 2.0 = 2000
        # Normal (rounds 11-20): 10 * 100 * 1.0 = 1000
        # Late (rounds 50-52): 3 * 100 * 0.5 = 150
        # Total dynamic base: 2000 + 1000 + 150 = 3150
        #
        # 8 consecutive failures, threshold 5 = 3 over
        # Penalty = (3+1) * 10% = 40%
        # Penalty points = 3150 * 40% = 1260 (based on dynamic score)
        # Adjusted = 3150 - 1260 = 1890

        base_score = calculate_team_base_score_with_dynamic(team, config)
        assert base_score == 3150, f"Expected 3150 base with mixed multipliers, got {base_score}"

        penalties = calculate_team_total_penalties(team, config)
        assert penalties == 1260, f"Expected 1260 penalty (40% of 3150 dynamic), got {penalties}"

        adjusted_score = calculate_team_adjusted_score(team, config)
        assert adjusted_score == 1890, f"Expected 1890 adjusted score, got {adjusted_score}"

    def test_multiple_teams_combined_scoring(self):
        """Test relative rankings with both features across multiple teams."""
        config = self._create_combined_config()

        # Team 1: All passes in early phase (best score)
        team1 = Team(name="Team Alpha", color="Blue")
        db.session.add(team1)
        service1 = Service(
            name="Service 1", check_name="ICMP", team=team1, host="1.1.1.1", port=0, points=100
        )
        db.session.add(service1)

        # Team 2: Some passes, no SLA violation
        team2 = Team(name="Team Beta", color="Blue")
        db.session.add(team2)
        service2 = Service(
            name="Service 2", check_name="ICMP", team=team2, host="2.2.2.2", port=0, points=100
        )
        db.session.add(service2)

        # Team 3: Some passes, with SLA violation
        team3 = Team(name="Team Gamma", color="Blue")
        db.session.add(team3)
        service3 = Service(
            name="Service 3", check_name="ICMP", team=team3, host="3.3.3.3", port=0, points=100
        )
        db.session.add(service3)

        db.session.commit()

        # Create 10 rounds (all early phase, 2x multiplier)
        for i in range(1, 11):
            round_obj = Round(number=i)
            db.session.add(round_obj)
            db.session.commit()

            # Team 1: All pass (10/10)
            check1 = Check(round=round_obj, service=service1)
            check1.finished(True, "Pass", "output", "command")
            db.session.add(check1)

            # Team 2: 8 pass, 2 fail, no consecutive streak >= 5
            # Pattern: PPPPPPFFPP
            result2 = i not in [7, 8]
            check2 = Check(round=round_obj, service=service2)
            check2.finished(result2, "Test", "output", "command")
            db.session.add(check2)

            # Team 3: 4 pass, then 6 fail (SLA violation)
            result3 = i <= 4
            check3 = Check(round=round_obj, service=service3)
            check3.finished(result3, "Test", "output", "command")
            db.session.add(check3)

        db.session.commit()

        # Team 1: 10 * 100 * 2.0 = 2000 dynamic, no penalty
        score1 = calculate_team_adjusted_score(team1, config)
        assert score1 == 2000, f"Team Alpha expected 2000, got {score1}"

        # Team 2: 8 * 100 * 2.0 = 1600 dynamic, no penalty (max consecutive failures = 2)
        score2 = calculate_team_adjusted_score(team2, config)
        assert score2 == 1600, f"Team Beta expected 1600, got {score2}"

        # Team 3 calculation:
        # Dynamic base: 4 * 100 * 2.0 = 800
        # 6 consecutive failures, threshold 5 = 1 over, penalty = (1+1)*10% = 20%
        # Penalty = 800 * 20% = 160 (based on dynamic score)
        # Adjusted = 800 - 160 = 640
        score3 = calculate_team_adjusted_score(team3, config)
        assert score3 == 640, f"Team Gamma expected 640, got {score3}"

        # Verify rankings: Team Alpha > Team Beta > Team Gamma
        assert score1 > score2 > score3, "Rankings should be Alpha > Beta > Gamma"

    def test_penalty_exceeds_multiplied_score_clamped_to_zero(self):
        """Test that penalty is clamped when it exceeds the dynamically-multiplied score.

        With allow_negative=False, the adjusted score should not go below 0.
        """
        team = Team(name="Penalty Clamp Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Clamp Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        db.session.add(service)
        db.session.commit()

        # Create rounds: 1 pass in late phase, then many failures
        # Late phase (0.5x): 1 * 100 * 0.5 = 50 dynamic base score
        # 10 failures = 5 over threshold = (5+1)*10% = 60% penalty (capped at 50%)
        # Penalty = 50 * 50% = 25 (based on dynamic score)
        # Adjusted = 50 - 25 = 25

        # Round 50: pass
        round_pass = Round(number=50)
        db.session.add(round_pass)
        db.session.commit()
        check_pass = Check(round=round_pass, service=service)
        check_pass.finished(True, "Pass", "output", "command")
        db.session.add(check_pass)

        # Rounds 51-60: 10 consecutive failures
        for i in range(51, 61):
            round_obj = Round(number=i)
            db.session.add(round_obj)
            db.session.commit()
            check = Check(round=round_obj, service=service)
            check.finished(False, "Fail", "output", "command")
            db.session.add(check)

        db.session.commit()

        config = self._create_combined_config()

        base_score = calculate_team_base_score_with_dynamic(team, config)
        assert base_score == 50, f"Expected 50 dynamic base score, got {base_score}"

        # 10 consecutive failures, penalty is capped at 50%
        penalty_percent = calculate_sla_penalty_percent(10, config)
        assert penalty_percent == 50, f"Expected 50% penalty (capped), got {penalty_percent}"

        penalties = calculate_team_total_penalties(team, config)
        assert penalties == 25, f"Expected 25 penalty points (50% of 50 dynamic), got {penalties}"

        # Adjusted = 50 - 25 = 25
        adjusted_score = calculate_team_adjusted_score(team, config)
        assert adjusted_score == 25, f"Expected 25 adjusted score, got {adjusted_score}"

    def test_combined_with_allow_negative(self):
        """Test combined scoring when allow_negative is True."""
        config = self._create_combined_config()
        config.allow_negative = True
        config.penalty_max_percent = 200  # Allow penalty > 100%

        # Create a team with mostly failures to generate large penalty
        team = Team(name="Negative Score Team", color="Blue")
        db.session.add(team)

        service = Service(
            name="Negative Service",
            check_name="ICMP",
            team=team,
            host="127.0.0.1",
            port=0,
            points=100,
        )
        db.session.add(service)
        db.session.commit()

        # 2 passes in late phase (0.5x), then 15 consecutive failures
        # Dynamic base: 2 * 100 * 0.5 = 100
        # 15 failures, threshold 5 = 10 over, penalty = (10+1)*10% = 110%
        # Penalty = 100 * 110% = 110 (based on dynamic score)
        # Adjusted = 100 - 110 = -10

        for i in range(50, 67):  # 17 rounds total
            round_obj = Round(number=i)
            db.session.add(round_obj)
            db.session.commit()
            result = i < 52  # rounds 50, 51 pass; 52-66 fail (15 failures)
            check = Check(round=round_obj, service=service)
            check.finished(result, "Test", "output", "command")
            db.session.add(check)

        db.session.commit()

        base_score = calculate_team_base_score_with_dynamic(team, config)
        assert base_score == 100, f"Expected 100 dynamic base score, got {base_score}"

        penalties = calculate_team_total_penalties(team, config)
        assert penalties == 110, f"Expected 110 penalty (110% of 100 dynamic), got {penalties}"

        adjusted_score = calculate_team_adjusted_score(team, config)
        assert adjusted_score == -10, f"Expected -10 with allow_negative, got {adjusted_score}"

    def test_dynamic_multiplier_on_failing_checks_no_score_contribution(self):
        """Test that failing checks don't contribute to score even with multipliers.

        Failing checks should contribute 0 points regardless of multiplier.
        Only the penalty calculation should consider the service's earned score.
        """
        config = self._create_combined_config()

        # Create a team with all failures in early phase
        # Should have 0 base score (no passes) and no penalty (0 to penalize)
        check_results = [False] * 10  # 10 failures
        team, service = self._create_team_with_rounds(check_results, points=100)

        base_score = calculate_team_base_score_with_dynamic(team, config)
        assert base_score == 0, "All failures should result in 0 base score"

        penalties = calculate_team_total_penalties(team, config)
        assert penalties == 0, "Penalty on 0 score should be 0"

        adjusted_score = calculate_team_adjusted_score(team, config)
        assert adjusted_score == 0, "Adjusted score should be 0"
