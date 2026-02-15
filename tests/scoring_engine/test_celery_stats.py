import mock

from scoring_engine.celery_stats import CeleryStats
from scoring_engine.db import db
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team


class InspectAll:
    def active_queues(self):
        return {"worker1": [{"name": "queue1"}]}

    def stats(self):
        return {
            "worker1": {
                "total": {"execute_command": 10},
                "pool": {"max-concurrency": 5},
                "uptime": 3600,
                "rusage": {"maxrss": 104857600, "utime": 12.5, "stime": 3.2},
            }
        }

    def active(self):
        return {"worker1": [1, 2]}

    def scheduled(self):
        return {"worker1": [1]}

    def reserved(self):
        return {"worker1": [1, 2, 3]}

    def ping(self):
        return [{"worker1": {"ok": "pong"}}]


class InspectNoQueues:
    def active_queues(self):
        return None

    def stats(self):
        return None

    def active(self):
        return None

    def scheduled(self):
        return None

    def reserved(self):
        return None

    def ping(self):
        return None


class Control:
    def __init__(self, inspect_obj):
        self._inspect_obj = inspect_obj

    def inspect(self, **kwargs):
        return self._inspect_obj


class TestCeleryStats:
    def create_service(self):
        team = Team(name="Team1", color="Blue")
        service = Service(
            name="svc1",
            team=team,
            check_name="TestCheck",
            host="127.0.0.1",
            worker_queue="queue1",
        )
        db.session.add(team)
        db.session.add(service)
        db.session.commit()

    def test_get_queue_stats(self):
        self.create_service()
        mock_app = mock.Mock()
        mock_app.control = Control(InspectAll())
        with mock.patch("scoring_engine.celery_stats.celery_app", mock_app):
            result = CeleryStats.get_queue_stats()
        assert result == [
            {
                "name": "queue1",
                "workers": ["worker1"],
                "services_running": "All",
                "running_tasks": 2,
                "scheduled_tasks": 1,
                "reserved_tasks": 3,
                "worker_count": 1,
            }
        ]

    def test_get_queue_stats_new_fields(self):
        """Test that queue stats include running/scheduled/reserved task counts."""
        self.create_service()
        mock_app = mock.Mock()
        mock_app.control = Control(InspectAll())
        with mock.patch("scoring_engine.celery_stats.celery_app", mock_app):
            result = CeleryStats.get_queue_stats()
        assert len(result) == 1
        queue = result[0]
        assert queue["running_tasks"] == 2
        assert queue["scheduled_tasks"] == 1
        assert queue["reserved_tasks"] == 3
        assert queue["worker_count"] == 1

    def test_get_worker_stats(self):
        self.create_service()
        mock_app = mock.Mock()
        mock_app.control = Control(InspectAll())
        with mock.patch("scoring_engine.celery_stats.celery_app", mock_app):
            with mock.patch("scoring_engine.celery_stats.platform") as mock_platform:
                mock_platform.system.return_value = "Darwin"
                result = CeleryStats.get_worker_stats()
        assert len(result) == 1
        worker = result[0]
        assert worker["worker_name"] == "worker1"
        assert worker["services_running"] == "All"
        assert worker["num_threads"] == 5
        assert worker["completed_tasks"] == 10
        assert worker["running_tasks"] == 2
        assert worker["worker_queues"] == ["queue1"]
        assert worker["utilization_pct"] == 40.0
        assert worker["uptime_seconds"] == 3600
        assert worker["max_rss_mb"] == 100.0
        assert worker["cpu_user_time"] == 12.5
        assert worker["cpu_system_time"] == 3.2
        assert worker["scheduled_tasks"] == 1
        assert worker["reserved_tasks"] == 3
        assert worker["is_alive"] is True

    def test_get_worker_stats_linux_rss(self):
        """Test that maxrss is converted from KB on Linux."""
        self.create_service()
        mock_app = mock.Mock()
        mock_app.control = Control(InspectAll())
        with mock.patch("scoring_engine.celery_stats.celery_app", mock_app):
            with mock.patch("scoring_engine.celery_stats.platform") as mock_platform:
                mock_platform.system.return_value = "Linux"
                result = CeleryStats.get_worker_stats()
        # On Linux, 104857600 KB = 102400 MB
        assert result[0]["max_rss_mb"] == 102400.0

    def test_get_worker_stats_no_workers(self):
        mock_app = mock.Mock()
        mock_app.control = Control(InspectNoQueues())
        with mock.patch("scoring_engine.celery_stats.celery_app", mock_app):
            result = CeleryStats.get_worker_stats()
        assert result == []

    def test_get_worker_summary(self):
        self.create_service()
        mock_app = mock.Mock()
        mock_app.control = Control(InspectAll())
        with mock.patch("scoring_engine.celery_stats.celery_app", mock_app):
            with mock.patch("scoring_engine.celery_stats.platform") as mock_platform:
                mock_platform.system.return_value = "Darwin"
                result = CeleryStats.get_worker_summary()
        assert result["total_workers"] == 1
        assert result["total_threads"] == 5
        assert result["total_running"] == 2
        assert result["total_completed"] == 10
        assert result["total_scheduled"] == 1
        assert result["avg_utilization_pct"] == 40.0

    def test_get_worker_summary_no_workers(self):
        mock_app = mock.Mock()
        mock_app.control = Control(InspectNoQueues())
        with mock.patch("scoring_engine.celery_stats.celery_app", mock_app):
            result = CeleryStats.get_worker_summary()
        assert result["total_workers"] == 0
        assert result["total_threads"] == 0
        assert result["total_running"] == 0
        assert result["total_completed"] == 0
        assert result["total_scheduled"] == 0
        assert result["avg_utilization_pct"] == 0
