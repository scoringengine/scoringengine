import pytest

from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestAbout:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        team = Team(name="Team 1", color="White")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        db.session.commit()

    def test_about(self):
        resp = self.client.get("/about")
        # TODO - Fix this
        # assert self.mock_obj.call_args == self.build_args(
        #     "about.html", version=version, about_content="example content value"
        # )
        assert resp.status_code == 200
