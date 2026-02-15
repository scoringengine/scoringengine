from scoring_engine.db import db
from scoring_engine.models.property import Property
from tests.scoring_engine.helpers import generate_sample_model_tree


class TestProperty:

    def test_init_property(self):
        property_obj = Property(name="testname", value="testvalue")
        assert property_obj.id is None
        assert property_obj.name == "testname"
        assert property_obj.value == "testvalue"
        assert property_obj.environment is None
        assert property_obj.environment_id is None

    def test_basic_property(self):
        environment = generate_sample_model_tree("Environment", db.session)
        property_obj = Property(name="ip", value="127.0.0.1", environment=environment)
        db.session.add(property_obj)
        db.session.commit()
        assert property_obj.id is not None
        assert property_obj.environment == environment
        assert property_obj.environment_id == environment.id
        assert property_obj.visible is False

    def test_nonhidden_property(self):
        environment = generate_sample_model_tree("Environment", db.session)
        property_obj = Property(name="ip", value="127.0.0.1", environment=environment, visible=True)
        db.session.add(property_obj)
        db.session.commit()
        assert property_obj.visible is True
