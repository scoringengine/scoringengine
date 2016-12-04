import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.property import Property

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest


class TestProperty(UnitTest):

    def test_init_property(self):
        property_obj = Property(name="testname", value="testvalue")
        assert property_obj.id is None
        assert property_obj.name == "testname"
        assert property_obj.value == "testvalue"
        assert property_obj.environment is None
        assert property_obj.environment_id is None

    def test_basic_property(self):
        environment = generate_sample_model_tree('Environment', self.db)
        property_obj = Property(name="ip", value="127.0.0.1", environment=environment)
        self.db.save(property_obj)
        assert property_obj.id is not None
        assert property_obj.environment == environment
        assert property_obj.environment_id == environment.id
        assert property_obj.visible is False

    def test_nonhidden_property(self):
        environment = generate_sample_model_tree('Environment', self.db)
        property_obj = Property(name="ip", value="127.0.0.1", environment=environment, visible=True)
        self.db.save(property_obj)
        assert property_obj.visible is True
