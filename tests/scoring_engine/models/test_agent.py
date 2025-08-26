from datetime import datetime

import pytz

from scoring_engine.models.agent import Agent
from scoring_engine.models.flag import FlagTypeEnum, Platform
from tests.scoring_engine.unit_test import UnitTest


class TestAgent(UnitTest):
    def test_as_dict(self):
        start = datetime(2024, 1, 1, tzinfo=pytz.UTC)
        end = datetime(2024, 1, 2, tzinfo=pytz.UTC)
        agent = Agent(
            id=1,
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"cmd": "ls"},
            start_time=start,
            end_time=end,
        )
        assert agent.as_dict() == {
            "id": 1,
            "type": "file",
            "data": {"cmd": "ls"},
            "start_time": int(start.timestamp()),
            "end_time": int(end.timestamp()),
        }
