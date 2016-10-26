class Job(object):
    def __init__(self, service_id, command, output=None):
        self.service_id = service_id
        self.command = command
        self.output = output

    def to_dict(self):
        return {
            "service_id": self.service_id,
            "command": self.command,
            "output": self.output
        }

    def from_dict(in_dict):
        job = Job(service_id=in_dict['service_id'], command=in_dict['command'])
        if in_dict['output']:
            job.output = in_dict['output']
        return job
