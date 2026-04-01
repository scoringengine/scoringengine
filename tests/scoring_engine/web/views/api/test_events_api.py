import json
from unittest.mock import patch

import pytest

from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestEventsTokenAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")
        db.session.add_all([self.white_team, self.blue_team, self.red_team])
        db.session.commit()

        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.blue_user = User(username="blueuser", password="testpass", team=self.blue_team)
        self.red_user = User(username="reduser", password="testpass", team=self.red_team)
        db.session.add_all([self.white_user, self.blue_user, self.red_user])
        db.session.commit()

    def _login(self, username):
        self.client.post("/login", data={"username": username, "password": "testpass"})

    @patch("scoring_engine.web.views.api.redis_lib")
    def test_anonymous_token(self, mock_redis_lib):
        mock_redis = mock_redis_lib.Redis.return_value
        resp = self.client.get("/api/events/token")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data

        # Check what was stored in Redis
        call_args = mock_redis.setex.call_args
        key = call_args[0][0]
        ttl = call_args[0][1]
        stored = json.loads(call_args[0][2])

        assert key.startswith("sse_token:")
        assert ttl == 300
        assert stored["role"] == "anonymous"
        assert stored["user_id"] is None
        assert stored["team_id"] is None

    @patch("scoring_engine.web.views.api.redis_lib")
    def test_blue_team_token(self, mock_redis_lib):
        mock_redis = mock_redis_lib.Redis.return_value
        self._login("blueuser")
        resp = self.client.get("/api/events/token")
        assert resp.status_code == 200

        stored = json.loads(mock_redis.setex.call_args[0][2])
        assert stored["role"] == "blue"
        assert stored["team_id"] == self.blue_team.id
        assert stored["user_id"] == self.blue_user.id

    @patch("scoring_engine.web.views.api.redis_lib")
    def test_white_team_token(self, mock_redis_lib):
        mock_redis = mock_redis_lib.Redis.return_value
        self._login("whiteuser")
        resp = self.client.get("/api/events/token")
        assert resp.status_code == 200

        stored = json.loads(mock_redis.setex.call_args[0][2])
        assert stored["role"] == "white"

    @patch("scoring_engine.web.views.api.redis_lib")
    def test_red_team_token(self, mock_redis_lib):
        mock_redis = mock_redis_lib.Redis.return_value
        self._login("reduser")
        resp = self.client.get("/api/events/token")
        assert resp.status_code == 200

        stored = json.loads(mock_redis.setex.call_args[0][2])
        assert stored["role"] == "red"

    @patch("scoring_engine.web.views.api.redis_lib")
    def test_token_is_unique(self, mock_redis_lib):
        mock_redis = mock_redis_lib.Redis.return_value
        resp1 = self.client.get("/api/events/token")
        resp2 = self.client.get("/api/events/token")
        assert resp1.get_json()["token"] != resp2.get_json()["token"]
