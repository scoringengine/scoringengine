import pytest

from sqlalchemy.exc import IntegrityError

from scoring_engine.models.machines import Machine
from scoring_engine.models.team import Team
from tests.scoring_engine.unit_test import UnitTest


class TestMachine(UnitTest):
    def test_init_machine(self):
        machine = Machine(name="host-1", team_id=1, status="healthy", compromised=True)

        assert machine.id is None
        assert machine.name == "host-1"
        assert machine.team_id == 1
        assert machine.status == "healthy"
        assert machine.compromised is True

    def test_machine_save_applies_defaults(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        machine = Machine(name="host-1", team_id=team.id)
        self.session.add(machine)
        self.session.commit()

        assert machine.id is not None
        assert machine.team_id == team.id
        assert machine.status == "unknown"
        assert machine.compromised is False

    def test_machine_name_is_required(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        machine = Machine(team_id=team.id)
        self.session.add(machine)

        with pytest.raises(IntegrityError):
            self.session.commit()

        self.session.rollback()
