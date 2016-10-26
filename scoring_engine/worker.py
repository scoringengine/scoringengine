from worker_queue import WorkerQueue


class Worker(object):

    def __init__(self):
        self.worker_queue = WorkerQueue()

    def run(self):
        import pdb
        pdb.set_trace()
