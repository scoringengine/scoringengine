from scoring_engine.db import session, engine
from scoring_engine.models.base import Base
from scoring_engine.models.setting import Setting


class UnitTest(object):
    def setup(self):
        self.session = session
        Base.metadata.drop_all(engine)
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
        worker_refresh_time_setting = Setting(name='worker_refresh_time', value=30)
        self.session.add(worker_refresh_time_setting)
        blue_team_update_hostname_setting = Setting(name='blue_team_update_hostname', value=True)
        session.add(blue_team_update_hostname_setting)
        blue_team_update_port_setting = Setting(name='blue_team_update_port', value=True)
        session.add(blue_team_update_port_setting)
        blue_team_update_account_usernames_setting = Setting(name='blue_team_update_account_usernames', value=True)
        session.add(blue_team_update_account_usernames_setting)
        blue_team_update_account_password_setting = Setting(name='blue_team_update_account_passwords', value=True)
        session.add(blue_team_update_account_password_setting)
        overview_show_round_info_setting = Setting(name='overview_show_round_info', value=True)
        session.add(overview_show_round_info_setting)
        self.session.commit()
