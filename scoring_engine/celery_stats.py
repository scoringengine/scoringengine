import platform

from sqlalchemy.orm import joinedload

from scoring_engine.celery_app import celery_app
from scoring_engine.db import db
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team


class CeleryStats:
    @staticmethod
    def _get_inspect_data():
        """Call all inspect methods once and return cached results."""
        inspector = celery_app.control.inspect(timeout=1.0)
        return {
            "active_queues": inspector.active_queues(),
            "stats": inspector.stats(),
            "active": inspector.active(),
            "scheduled": inspector.scheduled(),
            "reserved": inspector.reserved(),
            "ping": inspector.ping(),
        }

    @staticmethod
    def _summarize_services(services_running, all_services):
        """Summarize service lists: 'All' if worker handles every service, 'ALL' per-team if all team services."""
        total_running = sum(len(v) if isinstance(v, list) else 0 for v in services_running.values())
        if total_running == len(all_services):
            return "All"

        blue_teams = Team.get_all_blue_teams()
        for blue_team in blue_teams:
            if blue_team.name in services_running and isinstance(services_running[blue_team.name], list):
                if len(blue_team.services) == len(services_running[blue_team.name]):
                    services_running[blue_team.name] = "ALL"
        return services_running

    @staticmethod
    def get_queue_stats():
        finished_queue_facts = []
        queues_facts = {}

        all_services = db.session.query(Service).options(joinedload(Service.team)).all()
        for service in all_services:
            if service.worker_queue not in queues_facts:
                queues_facts[service.worker_queue] = {
                    "name": service.worker_queue,
                    "workers": [],
                    "services_running": {},
                    "running_tasks": 0,
                    "scheduled_tasks": 0,
                    "reserved_tasks": 0,
                    "worker_count": 0,
                }
            if service.team.name not in queues_facts[service.worker_queue]["services_running"]:
                queues_facts[service.worker_queue]["services_running"][service.team.name] = []
            queues_facts[service.worker_queue]["services_running"][service.team.name].append(service.name)

        # Summarize services per queue
        for queue_name, queue_facts in queues_facts.items():
            queue_facts["services_running"] = CeleryStats._summarize_services(
                queue_facts["services_running"], all_services
            )

        inspect_data = CeleryStats._get_inspect_data()
        active_queues = inspect_data["active_queues"]
        active_tasks = inspect_data["active"] or {}
        scheduled_tasks = inspect_data["scheduled"] or {}
        reserved_tasks = inspect_data["reserved"] or {}

        if active_queues is not None:
            # Build worker-to-queues mapping
            for worker_name, queues in active_queues.items():
                worker_queue_names = [q["name"] for q in queues]
                for queue_name in worker_queue_names:
                    if queue_name in queues_facts:
                        queues_facts[queue_name]["workers"].append(worker_name)
                        queues_facts[queue_name]["worker_count"] += 1

            # Aggregate task counts per queue
            for worker_name, queues in active_queues.items():
                worker_queue_names = [q["name"] for q in queues]
                worker_active = len(active_tasks.get(worker_name, []))
                worker_scheduled = len(scheduled_tasks.get(worker_name, []))
                worker_reserved = len(reserved_tasks.get(worker_name, []))
                for queue_name in worker_queue_names:
                    if queue_name in queues_facts:
                        queues_facts[queue_name]["running_tasks"] += worker_active
                        queues_facts[queue_name]["scheduled_tasks"] += worker_scheduled
                        queues_facts[queue_name]["reserved_tasks"] += worker_reserved

        for queue_name, queue_facts in queues_facts.items():
            finished_queue_facts.append(queue_facts)
        return finished_queue_facts

    @staticmethod
    def get_worker_stats():
        finished_worker_facts = []
        worker_facts = {}

        inspect_data = CeleryStats._get_inspect_data()
        active_queues = inspect_data["active_queues"]

        if active_queues is None:
            return finished_worker_facts

        for worker_name, queues in active_queues.items():
            queue_names = [queue["name"] for queue in queues]
            worker_facts[worker_name] = {
                "worker_queues": queue_names,
            }

        active_stats = inspect_data["stats"] or {}
        for worker_name, stats in active_stats.items():
            if worker_name not in worker_facts:
                continue
            completed_tasks = 0
            if "execute_command" in stats.get("total", {}):
                completed_tasks = stats["total"]["execute_command"]
            worker_facts[worker_name]["completed_tasks"] = completed_tasks
            worker_facts[worker_name]["num_threads"] = stats["pool"]["max-concurrency"]

            # Extract uptime
            worker_facts[worker_name]["uptime_seconds"] = stats.get("uptime", 0)

            # Extract resource usage
            rusage = stats.get("rusage", {})
            maxrss = rusage.get("maxrss", 0)
            # macOS reports maxrss in bytes, Linux in KB
            if platform.system() == "Darwin":
                worker_facts[worker_name]["max_rss_mb"] = round(maxrss / (1024 * 1024), 1)
            else:
                worker_facts[worker_name]["max_rss_mb"] = round(maxrss / 1024, 1)
            worker_facts[worker_name]["cpu_user_time"] = round(rusage.get("utime", 0), 2)
            worker_facts[worker_name]["cpu_system_time"] = round(rusage.get("stime", 0), 2)

        active_tasks_stats = inspect_data["active"] or {}
        for worker_name, stats in active_tasks_stats.items():
            if worker_name not in worker_facts:
                continue
            worker_facts[worker_name]["running_tasks"] = len(stats)

        # Extract scheduled/reserved counts
        scheduled_tasks = inspect_data["scheduled"] or {}
        reserved_tasks = inspect_data["reserved"] or {}
        ping_results = inspect_data["ping"] or {}

        # Build set of alive workers from ping response
        alive_workers = set()
        if ping_results:
            for entry in ping_results:
                if isinstance(entry, dict):
                    alive_workers.update(entry.keys())

        for worker_name in worker_facts:
            worker_facts[worker_name].setdefault("completed_tasks", 0)
            worker_facts[worker_name].setdefault("num_threads", 0)
            worker_facts[worker_name].setdefault("running_tasks", 0)
            worker_facts[worker_name].setdefault("uptime_seconds", 0)
            worker_facts[worker_name].setdefault("max_rss_mb", 0)
            worker_facts[worker_name].setdefault("cpu_user_time", 0)
            worker_facts[worker_name].setdefault("cpu_system_time", 0)
            worker_facts[worker_name]["scheduled_tasks"] = len(scheduled_tasks.get(worker_name, []))
            worker_facts[worker_name]["reserved_tasks"] = len(reserved_tasks.get(worker_name, []))
            worker_facts[worker_name]["is_alive"] = worker_name in alive_workers

            # Calculate utilization
            num_threads = worker_facts[worker_name]["num_threads"]
            running = worker_facts[worker_name]["running_tasks"]
            if num_threads > 0:
                worker_facts[worker_name]["utilization_pct"] = round(running / num_threads * 100, 1)
            else:
                worker_facts[worker_name]["utilization_pct"] = 0

        # Produce list of Service checks this worker will run
        all_services = db.session.query(Service).options(joinedload(Service.team)).all()
        for worker_name, facts in worker_facts.items():
            services_running = {}
            for service in all_services:
                if service.worker_queue in facts["worker_queues"]:
                    if service.team.name not in services_running:
                        services_running[service.team.name] = []
                    services_running[service.team.name].append(service.name)

            facts["services_running"] = CeleryStats._summarize_services(services_running, all_services)
            if not facts["services_running"]:
                facts["services_running"] = "None"

            finished_worker_facts.append(
                {
                    "worker_name": worker_name,
                    "services_running": facts["services_running"],
                    "num_threads": facts["num_threads"],
                    "completed_tasks": facts["completed_tasks"],
                    "running_tasks": facts["running_tasks"],
                    "worker_queues": facts["worker_queues"],
                    "utilization_pct": facts["utilization_pct"],
                    "uptime_seconds": facts["uptime_seconds"],
                    "max_rss_mb": facts["max_rss_mb"],
                    "cpu_user_time": facts["cpu_user_time"],
                    "cpu_system_time": facts["cpu_system_time"],
                    "scheduled_tasks": facts["scheduled_tasks"],
                    "reserved_tasks": facts["reserved_tasks"],
                    "is_alive": facts["is_alive"],
                }
            )
        return finished_worker_facts

    @staticmethod
    def _compute_summary(workers):
        """Compute aggregate summary from a pre-fetched worker stats list."""
        if not workers:
            return {
                "total_workers": 0,
                "total_threads": 0,
                "total_running": 0,
                "total_completed": 0,
                "total_scheduled": 0,
                "avg_utilization_pct": 0,
            }

        total_workers = len(workers)
        total_threads = sum(w["num_threads"] for w in workers)
        total_running = sum(w["running_tasks"] for w in workers)
        total_completed = sum(w["completed_tasks"] for w in workers)
        total_scheduled = sum(w["scheduled_tasks"] for w in workers)
        avg_utilization = round(sum(w["utilization_pct"] for w in workers) / total_workers, 1)

        return {
            "total_workers": total_workers,
            "total_threads": total_threads,
            "total_running": total_running,
            "total_completed": total_completed,
            "total_scheduled": total_scheduled,
            "avg_utilization_pct": avg_utilization,
        }

    @staticmethod
    def get_worker_summary():
        """Aggregate totals across all workers for stat cards."""
        return CeleryStats._compute_summary(CeleryStats.get_worker_stats())
