from tests.scoring_engine.web.web_test import WebTest
from tests.scoring_engine.helpers import populate_sample_data


class TestScoreboard(WebTest):

    def test_scoreboard(self):
        populate_sample_data(self.session)
        resp = self.client.get('/scoreboard')
        assert resp.status_code == 200
        assert self.mock_obj.call_args[0][0] == 'scoreboard.html'
        assert self.mock_obj.call_args[1]['team_labels'] == ['Blue Team 1']
        assert self.mock_obj.call_args[1]['team_scores'] == [100]
        assert self.mock_obj.call_args[1]['round_labels'] == ['Round 0', 'Round 1', 'Round 2']
        assert 'scores_colors' in self.mock_obj.call_args[1]
        assert self.mock_obj.call_args[1]['team_data'][1]['data'] == [0, 100, 100]
        assert self.mock_obj.call_args[1]['team_data'][1]['label'] == 'Blue Team 1'
        assert 'color' in self.mock_obj.call_args[1]['team_data'][1]
