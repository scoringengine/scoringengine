from scoring_engine.db import session, delete_db, init_db
from scoring_engine.models.setting import Setting


class UnitTest(object):
    def setup(self):
        self.session = session
        delete_db(self.session)
        init_db(self.session)
        self.create_default_settings()

    def teardown(self):
        delete_db(self.session)
        self.session.remove()

    def create_default_settings(self):
        self.session.add(
            Setting(name="about_page_content", value="example content value")
        )
        self.session.add(
            Setting(
                name="welcome_page_content", value="example welcome content <br>here"
            )
        )
        self.session.add(Setting(name="target_round_time", value=60))
        self.session.add(Setting(name="worker_refresh_time", value=30))
        self.session.add(Setting(name="engine_paused", value=False))
        self.session.add(Setting(name="pause_duration", value=30))
        self.session.add(Setting(name="blue_team_update_hostname", value=True))
        self.session.add(Setting(name="blue_team_update_port", value=True))
        self.session.add(Setting(name="blue_team_update_account_usernames", value=True))
        self.session.add(Setting(name="blue_team_update_account_passwords", value=True))
        self.session.add(Setting(name="blue_team_view_check_output", value=True))
        self.session.add(Setting(name="overview_show_round_info", value=True))
        self.session.commit()
