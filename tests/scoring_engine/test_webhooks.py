"""Tests for webhook notification functionality"""
from unittest.mock import patch

from scoring_engine.models.setting import Setting
from scoring_engine.webhooks import (
    detect_webhook_type,
    format_discord_message,
    format_generic_message,
    format_slack_message,
    get_webhook_config,
    notify_inject_graded,
    notify_round_complete,
    send_test_notification,
)
from tests.scoring_engine.unit_test import UnitTest


class TestWebhookHelpers(UnitTest):
    """Tests for webhook helper functions"""

    def test_detect_slack_webhook(self):
        """Test detection of Slack webhook URLs"""
        assert detect_webhook_type("https://hooks.slack.com/services/xxx") == "slack"
        assert detect_webhook_type("https://HOOKS.SLACK.COM/services/xxx") == "slack"

    def test_detect_discord_webhook(self):
        """Test detection of Discord webhook URLs"""
        assert detect_webhook_type("https://discord.com/api/webhooks/xxx") == "discord"
        assert (
            detect_webhook_type("https://discordapp.com/api/webhooks/xxx") == "discord"
        )

    def test_detect_generic_webhook(self):
        """Test detection of generic webhook URLs"""
        assert detect_webhook_type("https://example.com/webhook") == "generic"
        assert detect_webhook_type("") == "generic"
        assert detect_webhook_type(None) == "generic"

    def test_format_slack_message(self):
        """Test Slack message formatting"""
        result = format_slack_message("Test Title", "Test message", color="good")
        assert "attachments" in result
        assert result["attachments"][0]["title"] == "Test Title"
        assert result["attachments"][0]["text"] == "Test message"
        assert result["attachments"][0]["color"] == "good"

    def test_format_slack_message_with_fields(self):
        """Test Slack message formatting with fields"""
        fields = [{"title": "Field1", "value": "Value1"}]
        result = format_slack_message("Title", "Message", fields=fields)
        assert "fields" in result["attachments"][0]
        assert result["attachments"][0]["fields"][0]["title"] == "Field1"

    def test_format_discord_message(self):
        """Test Discord message formatting"""
        result = format_discord_message("Test Title", "Test message", color=0x00FF00)
        assert "embeds" in result
        assert result["embeds"][0]["title"] == "Test Title"
        assert result["embeds"][0]["description"] == "Test message"
        assert result["embeds"][0]["color"] == 0x00FF00

    def test_format_generic_message(self):
        """Test generic message formatting"""
        result = format_generic_message(
            "Title", "Message", "test_event", {"key": "value"}
        )
        assert result["event"] == "test_event"
        assert result["title"] == "Title"
        assert result["message"] == "Message"
        assert result["data"]["key"] == "value"


class TestWebhookConfig(UnitTest):
    """Tests for webhook configuration"""

    def setup_method(self):
        super(TestWebhookConfig, self).setup_method()
        # Create webhook settings
        self.session.add(Setting(name="webhook_enabled", value=False))
        self.session.add(Setting(name="webhook_url", value=""))
        self.session.add(Setting(name="webhook_on_round_complete", value=True))
        self.session.add(Setting(name="webhook_on_inject_graded", value=True))
        self.session.commit()

    def teardown_method(self):
        Setting.clear_cache()
        super(TestWebhookConfig, self).teardown_method()

    def test_get_webhook_config_disabled(self):
        """Test getting config when webhooks are disabled"""
        Setting.clear_cache()
        config = get_webhook_config()
        assert config is None

    def test_get_webhook_config_enabled(self):
        """Test getting config when webhooks are enabled"""
        setting = Setting.get_setting("webhook_enabled")
        setting.value = True
        self.session.commit()
        Setting.clear_cache()

        url_setting = Setting.get_setting("webhook_url")
        url_setting.value = "https://hooks.slack.com/test"
        self.session.commit()
        Setting.clear_cache()

        config = get_webhook_config()
        assert config is not None
        assert config["enabled"] is True
        assert config["url"] == "https://hooks.slack.com/test"


class TestWebhookNotifications(UnitTest):
    """Tests for webhook notification functions"""

    def setup_method(self):
        super(TestWebhookNotifications, self).setup_method()
        # Create webhook settings with everything enabled
        self.session.add(Setting(name="webhook_enabled", value=True))
        self.session.add(
            Setting(name="webhook_url", value="https://hooks.slack.com/test")
        )
        self.session.add(Setting(name="webhook_on_round_complete", value=True))
        self.session.add(Setting(name="webhook_on_inject_graded", value=True))
        self.session.commit()
        Setting.clear_cache()

    def teardown_method(self):
        Setting.clear_cache()
        super(TestWebhookNotifications, self).teardown_method()

    @patch("scoring_engine.webhooks.send_webhook")
    def test_notify_round_complete(self, mock_send):
        """Test round completion notification"""
        mock_send.return_value = True
        Setting.clear_cache()

        result = notify_round_complete(
            5, stats={"passed": 10, "failed": 2, "total": 12}
        )

        assert result is True
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert "hooks.slack.com" in call_args[0][0]  # URL
        assert "slack" in call_args[0][2]  # webhook_type

    @patch("scoring_engine.webhooks.send_webhook")
    def test_notify_inject_graded(self, mock_send):
        """Test inject graded notification"""
        mock_send.return_value = True
        Setting.clear_cache()

        result = notify_inject_graded("Team 1", "Test Inject", 80, 100)

        assert result is True
        mock_send.assert_called_once()

    @patch("scoring_engine.webhooks.send_webhook")
    def test_notify_disabled_when_setting_off(self, mock_send):
        """Test that notifications are not sent when setting is disabled"""
        setting = Setting.get_setting("webhook_on_round_complete")
        setting.value = False
        self.session.commit()
        Setting.clear_cache()

        result = notify_round_complete(5)

        assert result is False
        mock_send.assert_not_called()

    @patch("scoring_engine.webhooks.send_webhook")
    def test_send_test_notification(self, mock_send):
        """Test sending a test notification"""
        mock_send.return_value = True
        Setting.clear_cache()

        success, message = send_test_notification()

        assert success is True
        assert "success" in message.lower()
        mock_send.assert_called_once()
