from sqlalchemy.orm import joinedload

from scoring_engine.celery_app import celery_app
from scoring_engine.db import db
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.worker_packs import queue_for_service


class CeleryStats:
    @staticmethod
    def get_queue_stats():
        finished_queue_facts = []

        queues_facts = {}

        all_services = db.session.query(Service).options(joinedload(Service.team)).all()
        for service in all_services:
            # Group by the queue checks are actually sent to, which includes the
            # tool pack (e.g. "main.browser"). A pack queue with no workers means
            # those checks will never run.
            queue = queue_for_service(service)
            if queue not in queues_facts:
                queues_facts[queue] = {
                    "name": queue,
                    "workers": [],
                    "services_running": {},
                }
            queues_facts[queue]["services_running"].setdefault(service.team.name, []).append(service.name)

        for queue_name, queue_facts in queues_facts.items():
            # If all of the services are listed for this specific worker, let's just alias it as 'All'
            queue_services_total_running = sum(len(svcs) for svcs in queue_facts["services_running"].values())
            if queue_services_total_running == len(all_services):
                queue_facts["services_running"] = "All"
            else:
                blue_teams = Team.get_all_blue_teams()
                for blue_team in blue_teams:
                    if blue_team.name in queue_facts["services_running"] and len(blue_team.services) == len(
                        queue_facts["services_running"][blue_team.name]
                    ):
                        # Summarize it for each team if the worker runs all services
                        queue_facts["services_running"][blue_team.name] = "ALL"

        # Get which workers are assigned to which queues
        active_queues = celery_app.control.inspect().active_queues()
        for queue_name, queue_facts in queues_facts.items():
            # If we don't have any queues, we also have no workers
            if active_queues is not None:
                for worker_name, queues in active_queues.items():
                    if queue_name in [k["name"] for k in queues]:
                        queue_facts["workers"].append(worker_name)

        for queue_name, queue_facts in queues_facts.items():
            finished_queue_facts.append(queue_facts)
        return finished_queue_facts

    @staticmethod
    def get_worker_stats():
        finished_worker_facts = []
        worker_facts = {}

        # Get which workers are assigned to which queues
        active_queues = celery_app.control.inspect().active_queues()
        # If we don't have any queues, we also have no workers
        if active_queues is None:
            return finished_worker_facts

        for worker_name, queues in active_queues.items():
            queue_names = []
            for queue in queues:
                queue_names.append(queue["name"])
            worker_facts[worker_name] = {
                "worker_queues": queue_names,
            }

        # Get worker stats about completed tasks and such
        active_stats = celery_app.control.inspect().stats()
        for worker_name, stats in active_stats.items():
            completed_tasks = 0
            if "execute_command" in stats["total"]:
                completed_tasks = stats["total"]["execute_command"]
            worker_facts[worker_name]["completed_tasks"] = completed_tasks
            worker_facts[worker_name]["num_threads"] = stats["pool"]["max-concurrency"]

        # Get worker stats about currently running tasks
        active_tasks_stats = celery_app.control.inspect().active()
        for worker_name, stats in active_tasks_stats.items():
            worker_facts[worker_name]["running_tasks"] = len(stats)

        # Produce list of Service checks this worker will run
        all_services = db.session.query(Service).options(joinedload(Service.team)).all()
        for worker_name, facts in worker_facts.items():
            facts["services_running"] = []
            services_running = {}
            for service in all_services:
                if queue_for_service(service) in facts["worker_queues"]:
                    if service.team.name not in services_running:
                        services_running[service.team.name] = []
                    services_running[service.team.name].append(service.name)
            # If all of the services are listed for this specific worker, let's just alias it as 'All'
            worker_services_total_running = 0
            for team_name, team_services in services_running.items():
                worker_services_total_running += len(team_services)
            if worker_services_total_running == len(all_services):
                facts["services_running"] = "All"
            else:
                facts["services_running"] = services_running
                blue_teams = Team.get_all_blue_teams()
                for blue_team in blue_teams:
                    if blue_team.name in services_running and len(blue_team.services) == len(
                        services_running[blue_team.name]
                    ):
                        # Summarize it for each team if the worker runs all services
                        facts["services_running"][blue_team.name] = "ALL"

            # Instead of an empty string in the table, let's tell them None
            if len(facts["services_running"]) == 0:
                facts["services_running"] = "None"
            # Clean up services_running

            finished_worker_facts.append(
                {
                    "worker_name": worker_name,
                    "services_running": facts["services_running"],
                    "num_threads": facts["num_threads"],
                    "completed_tasks": facts["completed_tasks"],
                    "running_tasks": facts["running_tasks"],
                    "worker_queues": facts["worker_queues"],
                }
            )
        return finished_worker_facts
