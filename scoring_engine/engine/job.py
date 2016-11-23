class Job(object):
    def __init__(self, environment_id, command):
        self.environment_id = environment_id
        self.command = command
        self.output = None
        self.result = None
        self.reason = None
        self.finished = False

    def to_dict(self):
        initial_dict = {
            "environment_id": self.environment_id,
            "command": self.command,
            "finished": self.finished,
        }
        if self.output is not None:
            initial_dict['output'] = self.output
        if self.result is not None:
            initial_dict['result'] = self.result
        if self.reason is not None:
            initial_dict['reason'] = self.reason

        return initial_dict

    def set_output(self, output):
        self.output = output
        self.finished = True

    def set_fail(self, reason):
        self.finished = True
        self.result = 'Fail'
        self.reason = reason

    def set_pass(self):
        self.result = 'Pass'
        self.finished = True

    def completed(self):
        return self.finished is True

    def passed(self):
        return self.result == 'Pass'

    def from_dict(in_dict):
        job = Job(environment_id=in_dict['environment_id'], command=in_dict['command'])
        if 'output' in in_dict:
            job.output = in_dict['output']
        if 'result' in in_dict:
            job.result = in_dict['result']
        if 'finished' in in_dict:
            job.finished = in_dict['finished']
        if 'reason' in in_dict:
            job.reason = in_dict['reason']
        return job
