import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.config import Config


class TestConfig(object):

    def setup(self):
        self.config = Config(location="../../tests/scoring_engine/engine/example.conf")

    def test_checks_location(self):
        assert self.config.checks_location == "scoring_engine.engine.checks"

    def test_check_timeout(self):
        assert self.config.check_timeout == 30

    def test_db_uri(self):
        assert self.config.db_uri == "sqlite:////tmp/test_engine.db"

    def test_redis_host(self):
        assert self.config.redis_host == "127.0.0.1"

    def test_redis_port(self):
        assert self.config.redis_port == 6379

    def test_redis_password(self):
        assert self.config.redis_password == "testpass"

    def test_redis_namespace(self):
        assert self.config.redis_namespace == "scoring_engine"

    def test_sponsorship_images(self):
        assert len(self.config.sponsorship_images) == 4
        assert self.config.sponsorship_images[0] == {'images': ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg'], 'sponsorship_level': 'diamond'}
        assert self.config.sponsorship_images[1] == {'images': ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg'], 'sponsorship_level': 'platinum'}
        assert self.config.sponsorship_images[2] == {'images': ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg'], 'sponsorship_level': 'somecustomlevel'}
        assert self.config.sponsorship_images[3] == {'images': ['/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg', '/static/images/logo-placeholder.jpg'], 'sponsorship_level': 'gold'}
