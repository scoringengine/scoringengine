import mock

from scoring_engine.celery_stats import CeleryStats
from scoring_engine.models.team import Team
from scoring_engine.models.service import Service

from tests.scoring_engine.unit_test import UnitTest


class InspectAll:
    def active_queues(self):
        return {'worker1': [{'name': 'queue1'}]}

    def stats(self):
        return {
            'worker1': {
                'total': {'execute_command': 10},
                'pool': {'max-concurrency': 5},
            }
        }

    def active(self):
        return {'worker1': [1, 2]}


class InspectNoQueues:
    def active_queues(self):
        return None


class Control:
    def __init__(self, inspect_obj):
        self._inspect_obj = inspect_obj

    def inspect(self):
        return self._inspect_obj


class TestCeleryStats(UnitTest):
    def create_service(self):
        team = Team(name='Team1', color='Blue')
        service = Service(
            name='svc1',
            team=team,
            check_name='TestCheck',
            host='127.0.0.1',
            worker_queue='queue1',
        )
        self.session.add(team)
        self.session.add(service)
        self.session.commit()

    def test_get_queue_stats(self):
        self.create_service()
        mock_app = mock.Mock()
        mock_app.control = Control(InspectAll())
        with mock.patch('scoring_engine.celery_stats.celery_app', mock_app):
            result = CeleryStats.get_queue_stats()
        assert result == [
            {
                'name': 'queue1',
                'workers': ['worker1'],
                'services_running': 'All',
            }
        ]

    def test_get_worker_stats(self):
        self.create_service()
        mock_app = mock.Mock()
        mock_app.control = Control(InspectAll())
        with mock.patch('scoring_engine.celery_stats.celery_app', mock_app):
            result = CeleryStats.get_worker_stats()
        assert result == [
            {
                'worker_name': 'worker1',
                'services_running': 'All',
                'num_threads': 5,
                'completed_tasks': 10,
                'running_tasks': 2,
                'worker_queues': ['queue1'],
            }
        ]

    def test_get_worker_stats_no_workers(self):
        mock_app = mock.Mock()
        mock_app.control = Control(InspectNoQueues())
        with mock.patch('scoring_engine.celery_stats.celery_app', mock_app):
            result = CeleryStats.get_worker_stats()
        assert result == []
