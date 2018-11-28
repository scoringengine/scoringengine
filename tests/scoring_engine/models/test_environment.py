from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property

from tests.scoring_engine.helpers import generate_sample_model_tree
from tests.scoring_engine.unit_test import UnitTest


class TestEnvironment(UnitTest):

    def test_init_service(self):
        environment = Environment(matching_content='*')
        assert environment.id is None
        assert environment.properties == []
        assert environment.matching_content == '*'

    def test_basic_service(self):
        service = generate_sample_model_tree('Service', self.session)
        environment = Environment(service=service, matching_content='*')
        self.session.add(environment)
        property_1 = Property(name='example_property1', value='somevalue', environment=environment)
        property_2 = Property(name='example_property2', value='anotheralue', environment=environment)
        self.session.add(property_1)
        self.session.add(property_2)
        self.session.commit()
        assert environment.id is not None
        assert environment.service_id == service.id
        assert environment.service == service
        assert environment.properties == [property_1, property_2]
