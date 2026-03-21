"""Tests for Agent API endpoints - verifies checkin persists solves to DB"""

from datetime import datetime, timedelta, timezone

import pytest

from scoring_engine.db import db
from scoring_engine.models.flag import Flag, FlagTypeEnum, Perm, Platform, Solve
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.web.views.api.agent import BtaPayloadEncryption


class TestAgentCheckinAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        self.psk = "testpsk123"
        db.session.add(Setting(name="agent_psk", value=self.psk))
        db.session.add(Setting(name="agent_show_flag_early_mins", value="5"))
        db.session.add(Setting(name="agent_checkin_interval_sec", value="60"))
        db.session.commit()

        self.blue_team = Team(name="Blue Team 1", color="Blue")
        db.session.add(self.blue_team)
        db.session.commit()

    def _checkin(self, team_name, host, platform, flags=None):
        crypter = BtaPayloadEncryption(self.psk, team_name)
        payload = {
            "team": team_name,
            "host": host,
            "plat": platform,
        }
        if flags is not None:
            payload["flags"] = flags
        return self.client.post(
            f"/api/agent/checkin?t={team_name}",
            data=crypter.dumps(payload),
            content_type="application/octet-stream",
        )

    def test_checkin_persists_solves_to_database(self):
        """Verify that flag solves submitted via agent checkin are committed to the DB."""
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\flag.txt", "content": "flag{test}"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        db.session.add(flag)
        db.session.commit()

        resp = self._checkin("Blue Team 1", "192.168.1.10", "win", flags=[flag.id])
        assert resp.status_code == 200

        solves = db.session.query(Solve).all()
        assert len(solves) == 1
        assert solves[0].flag_id == flag.id
        assert solves[0].host == "192.168.1.10"
        assert solves[0].team_id == self.blue_team.id

    def test_checkin_without_flags_persists_nothing(self):
        """Checkin with no flags should not create any solves."""
        resp = self._checkin("Blue Team 1", "192.168.1.10", "win", flags=[])
        assert resp.status_code == 200

        solves = db.session.query(Solve).all()
        assert len(solves) == 0

    def test_checkin_ignores_dummy_flags(self):
        """Dummy flags should be filtered out and not create solves."""
        dummy_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\dummy.txt", "content": "dummy"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=True,
        )
        db.session.add(dummy_flag)
        db.session.commit()

        resp = self._checkin("Blue Team 1", "192.168.1.10", "win", flags=[dummy_flag.id])
        assert resp.status_code == 200

        solves = db.session.query(Solve).all()
        assert len(solves) == 0

    def test_checkin_bad_team_returns_400(self):
        """Non-existent team should return 400."""
        resp = self._checkin("Nonexistent Team", "192.168.1.10", "win")
        assert resp.status_code == 400
