from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from scoring_engine.models.machines import Machine
from scoring_engine.models.team import Team
from tests.scoring_engine.unit_test import UnitTest


class TestMachine(UnitTest):
    def test_init_machine(self):
        machine = Machine(name="host-1", team_id=1, status=Machine.STATUS_HEALTHY)

        assert machine.id is None
        assert machine.name == "host-1"
        assert machine.team_id == 1
        assert machine.status == Machine.STATUS_HEALTHY
        assert machine.last_check_in_at is None
        assert machine.last_status_change_at is None

    def test_machine_save_applies_defaults(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        machine = Machine(name="host-1", team_id=team.id)
        self.session.add(machine)
        self.session.commit()

        assert machine.id is not None
        assert machine.team_id == team.id
        assert machine.status == Machine.STATUS_UNKNOWN
        assert machine.last_check_in_at is None
        assert machine.last_status_change_at is None

    def test_machine_name_is_required(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        machine = Machine(team_id=team.id)
        self.session.add(machine)

        with pytest.raises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_mark_check_in_sets_timestamp(self):
        machine = Machine(name="host-1", team_id=1)
        now = datetime.utcnow()

        machine.mark_check_in(now)

        assert machine.last_check_in_at == now

    def test_update_status_sets_last_status_change_at_when_changed(self):
        machine = Machine(name="host-1", team_id=1, status=Machine.STATUS_UNKNOWN)
        now = datetime.utcnow()

        machine.update_status(Machine.STATUS_HEALTHY, now)

        assert machine.status == Machine.STATUS_HEALTHY
        assert machine.last_status_change_at == now

    def test_update_status_does_not_change_timestamp_when_same_status(self):
        original = datetime.utcnow() - timedelta(minutes=1)
        machine = Machine(
            name="host-1",
            team_id=1,
            status=Machine.STATUS_HEALTHY,
            last_status_change_at=original,
        )

        machine.update_status(Machine.STATUS_HEALTHY, datetime.utcnow())

        assert machine.status == Machine.STATUS_HEALTHY
        assert machine.last_status_change_at == original