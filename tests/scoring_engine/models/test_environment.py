import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest


class TestEnvironment(UnitTest):

    def test_init_service(self):
        environment = Environment(matching_regex='*')
        assert environment.id is None
        assert environment.properties == []
        assert environment.matching_regex == '*'

    def test_basic_service(self):
        service = generate_sample_model_tree('Service', self.db)
        environment = Environment(service=service, matching_regex='*')
        self.db.save(environment)
        property_1 = Property(name='example_property1', value='somevalue', environment=environment)
        property_2 = Property(name='example_property2', value='anotheralue', environment=environment)
        self.db.save(property_1)
        self.db.save(property_2)
        assert environment.id is not None
        assert environment.service_id == service.id
        assert environment.service == service
        assert environment.properties == [property_1, property_2]
