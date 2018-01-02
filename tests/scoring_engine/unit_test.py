from scoring_engine.db import session, engine
from scoring_engine.models.base import Base
from scoring_engine.models.setting import Setting


class UnitTest(object):
    def setup(self):
        self.session = session
        Base.metadata.create_all(engine)
        self.create_default_settings()

    def teardown(self):
        Base.metadata.drop_all(engine)
        self.session.close_all()

    def create_default_settings(self):
        about_page_setting = Setting(name='about_page_content', value='example content value')
        self.session.add(about_page_setting)
        welcome_page_setting = Setting(name='welcome_page_content', value='example welcome content <br>here')
        self.session.add(welcome_page_setting)
        round_time_sleep_setting = Setting(name='round_time_sleep', value=60)
        self.session.add(round_time_sleep_setting)
        self.session.commit()
