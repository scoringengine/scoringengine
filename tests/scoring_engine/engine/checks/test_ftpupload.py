from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.account import Account

from tests.scoring_engine.unit_test import UnitTest


class TestFTPUploadCheck(UnitTest):
    def test_ftpupload_check(self):
        engine = Engine()
        service = Service(name='Example Service', check_name='FTPUploadCheck', ip_address='127.0.0.1')
        account = Account(username='techy', password='techy', service=service)
        environment = Environment(service=service, matching_regex='> STOR foo.txt')
        prop1 = Property(environment=environment, name='filename', value='foo.txt')
        self.db.save(service)
        self.db.save(account)
        self.db.save(environment)
        self.db.save(prop1)
        dns_check_obj = engine.check_name_to_obj('FTPUploadCheck')(environment)
        assert dns_check_obj.command() == 'echo "cyberengine check" | curl -s -S -4 -v --ftp-pasv --ftp-create-dirs -T - ftp://techy:techy@127.0.0.1/foo.txt'
