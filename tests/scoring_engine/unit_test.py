from scoring_engine.db import db, delete_db, init_db
from scoring_engine.models.setting import Setting
from scoring_engine.web import create_app


class UnitTest(object):
    def setup_method(self):
        # Create Flask app and application context for Flask-SQLAlchemy
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Backward compatibility - many tests use self.session
        self.session = db.session

        delete_db()
        init_db()
        self.create_default_settings()

    def teardown_method(self):
        delete_db()
        db.session.remove()
        # Only pop context if it hasn't been popped already
        # (some child classes may pop before calling super)
        if hasattr(self, 'ctx') and self.ctx._cv_tokens:
            self.ctx.pop()

    def create_default_settings(self):
        db.session.add(
            Setting(name="about_page_content", value="example content value")
        )
        db.session.add(
            Setting(
                name="welcome_page_content", value="example welcome content <br>here"
            )
        )
        db.session.add(Setting(name="target_round_time", value=60))
        db.session.add(Setting(name="worker_refresh_time", value=30))
        db.session.add(Setting(name="engine_paused", value=False))
        db.session.add(Setting(name="pause_duration", value=30))
        db.session.add(Setting(name="blue_team_update_hostname", value=True))
        db.session.add(Setting(name="blue_team_update_port", value=True))
        db.session.add(Setting(name="blue_team_update_account_usernames", value=True))
        db.session.add(Setting(name="blue_team_update_account_passwords", value=True))
        db.session.add(Setting(name="blue_team_view_check_output", value=True))
        db.session.add(Setting(name="blue_team_view_status_page", value=True))
        db.session.add(Setting(name="overview_show_round_info", value=True))
        # SLA Penalty Settings
        db.session.add(Setting(name="sla_enabled", value=False))
        db.session.add(Setting(name="sla_penalty_threshold", value="5"))
        db.session.add(Setting(name="sla_penalty_percent", value="10"))
        db.session.add(Setting(name="sla_penalty_max_percent", value="50"))
        db.session.add(Setting(name="sla_penalty_mode", value="additive"))
        db.session.add(Setting(name="sla_allow_negative", value=False))
        # Dynamic Scoring Settings
        db.session.add(Setting(name="dynamic_scoring_enabled", value=False))
        db.session.add(Setting(name="dynamic_scoring_early_rounds", value="10"))
        db.session.add(Setting(name="dynamic_scoring_early_multiplier", value="2.0"))
        db.session.add(Setting(name="dynamic_scoring_late_start_round", value="50"))
        db.session.add(Setting(name="dynamic_scoring_late_multiplier", value="0.5"))
        db.session.commit()
