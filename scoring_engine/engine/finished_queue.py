from scoring_engine.engine.job_queue import JobQueue


class FinishedQueue(JobQueue):
    def __init__(self):
        super(FinishedQueue, self).__init__()
        self.queue_name = "finished"
