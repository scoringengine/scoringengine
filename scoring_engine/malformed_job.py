class MalformedJob(Exception):
    def __str__(self):
        return "Job must be of instance of Job class"

