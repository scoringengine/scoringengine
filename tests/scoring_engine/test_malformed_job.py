import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from malformed_job import MalformedJob


class TestMalformedJob(object):

    def test_init(self):
        exception = MalformedJob()
        assert str(exception) == 'Job must be of instance of Job class'
