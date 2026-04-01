import json
from unittest.mock import MagicMock, patch

from scoring_engine.events import publish_event, should_send_event


class TestPublishEvent:
    @patch("scoring_engine.events._get_redis")
    def test_publishes_to_redis(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        publish_event("round_complete", {"round": 5})

        mock_redis.publish.assert_called_once()
        channel, message = mock_redis.publish.call_args[0]
        assert channel == "se:events"
        payload = json.loads(message)
        assert payload["type"] == "round_complete"
        assert payload["data"]["round"] == 5
        assert payload["visibility"] == "public"
        assert payload["team_id"] is None

    @patch("scoring_engine.events._get_redis")
    def test_publishes_team_event(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        publish_event("inject_update", {"inject_id": 42}, visibility="blue", team_id=5)

        payload = json.loads(mock_redis.publish.call_args[0][1])
        assert payload["visibility"] == "blue"
        assert payload["team_id"] == 5

    @patch("scoring_engine.events._get_redis")
    def test_publish_swallows_errors(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_redis.publish.side_effect = ConnectionError("Redis down")
        mock_get_redis.return_value = mock_redis

        # Should not raise
        publish_event("round_complete")


class TestShouldSendEvent:
    def test_public_event_visible_to_all(self):
        event = {"type": "round_complete", "visibility": "public", "team_id": None}
        assert should_send_event(event, "anonymous", None)
        assert should_send_event(event, "blue", 5)
        assert should_send_event(event, "red", 1)
        assert should_send_event(event, "white", 1)

    def test_blue_event_filtered_by_team(self):
        event = {"type": "inject_update", "visibility": "blue", "team_id": 5}
        assert should_send_event(event, "blue", 5)
        assert not should_send_event(event, "blue", 6)
        assert not should_send_event(event, "anonymous", None)

    def test_white_sees_all_events(self):
        event = {"type": "inject_update", "visibility": "blue", "team_id": 5}
        assert should_send_event(event, "white", 1)

    def test_red_event_visible_to_red(self):
        event = {"type": "flag_update", "visibility": "red", "team_id": None}
        assert should_send_event(event, "red", 1)
        assert not should_send_event(event, "blue", 5)
        assert should_send_event(event, "white", 1)

    def test_unknown_visibility_denied(self):
        event = {"type": "test", "visibility": "unknown", "team_id": None}
        assert not should_send_event(event, "blue", 5)
        assert should_send_event(event, "white", 1)
