from web_test import WebTest
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestProfile(WebTest):

    def setup(self):
        super(TestProfile, self).setup()
        team1 = Team(name="Team 1", color="White")
        self.db.save(team1)
        user1 = User(username='testuser', password='testpass', team=team1)
        self.db.save(user1)

    def test_home_auth_required(self):
        self.verify_auth_required('/profile')

    def test_home_with_auth(self):
        self.client.login('testuser', 'testpass')
        resp = self.client.get('/profile')
        assert resp.status_code == 200
