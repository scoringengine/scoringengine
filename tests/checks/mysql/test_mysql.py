import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.property import Property

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))
from unit_test import UnitTest

class TestMySQLCheck(UnitTest):

    def test_mysql_check(self):
        engine = Engine()
        service = Service(name="Example MySQL Service", check_name="MySQL Check")
        mysql_properties = Property(host="127.0.0.1", username="testuser", password="testpass", database="test", mysql_cmd="show tables")
        self.db.save(service)
        self.db.save(mysql_properties)
        mysql_check_obj = engine.checks[0](service)
        assert mysql_check_obj.command() == 'mysql -h %s -u %s -p %s %s -e %s' %(host, username, password, database, mysql_cmd)
