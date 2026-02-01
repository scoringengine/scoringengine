"""Webhook notification system for Slack, Discord, and generic webhooks.

This module provides functions to send notifications to external services
when competition events occur (round completion, inject grading, etc.).
"""
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scoring_engine.models.setting import Setting

logger = logging.getLogger(__name__)


def get_webhook_config():
    """Get webhook configuration from settings.

    Returns a dict with webhook settings, or None if not configured.
    """
    enabled_setting = Setting.get_setting("webhook_enabled")
    if not enabled_setting or not enabled_setting.value:
        return None

    url_setting = Setting.get_setting("webhook_url")
    if not url_setting or not url_setting.value:
        return None

    return {
        "enabled": True,
        "url": url_setting.value,
        "on_round_complete": Setting.get_setting("webhook_on_round_complete").value
        if Setting.get_setting("webhook_on_round_complete")
        else True,
        "on_inject_graded": Setting.get_setting("webhook_on_inject_graded").value
        if Setting.get_setting("webhook_on_inject_graded")
        else True,
    }


def detect_webhook_type(url):
    """Detect webhook type from URL.

    Returns 'slack', 'discord', or 'generic'.
    """
    if not url:
        return "generic"

    url_lower = url.lower()
    if "hooks.slack.com" in url_lower:
        return "slack"
    elif (
        "discord.com/api/webhooks" in url_lower
        or "discordapp.com/api/webhooks" in url_lower
    ):
        return "discord"
    return "generic"


def format_slack_message(title, message, color="good", fields=None):
    """Format a message for Slack webhook.

    Args:
        title: Message title
        message: Main message text
        color: Attachment color ('good', 'warning', 'danger', or hex)
        fields: Optional list of field dicts with 'title' and 'value' keys

    Returns:
        Dict formatted for Slack incoming webhook
    """
    attachment = {
        "fallback": f"{title}: {message}",
        "color": color,
        "title": title,
        "text": message,
        "footer": "Scoring Engine",
    }

    if fields:
        attachment["fields"] = [
            {
                "title": f["title"],
                "value": str(f["value"]),
                "short": f.get("short", True),
            }
            for f in fields
        ]

    return {"attachments": [attachment]}


def format_discord_message(title, message, color=0x00FF00, fields=None):
    """Format a message for Discord webhook.

    Args:
        title: Embed title
        message: Main message text
        color: Embed color as integer (default green)
        fields: Optional list of field dicts with 'title' and 'value' keys

    Returns:
        Dict formatted for Discord webhook
    """
    embed = {
        "title": title,
        "description": message,
        "color": color,
        "footer": {"text": "Scoring Engine"},
    }

    if fields:
        embed["fields"] = [
            {
                "name": f["title"],
                "value": str(f["value"]),
                "inline": f.get("short", True),
            }
            for f in fields
        ]

    return {"embeds": [embed]}


def format_generic_message(title, message, event_type, data=None):
    """Format a message for generic webhook.

    Args:
        title: Message title
        message: Main message text
        event_type: Event type identifier
        data: Optional dict with additional data

    Returns:
        Dict with generic webhook payload
    """
    payload = {
        "event": event_type,
        "title": title,
        "message": message,
        "source": "scoring_engine",
    }

    if data:
        payload["data"] = data

    return payload


def send_webhook(url, payload, webhook_type="generic"):
    """Send a webhook notification.

    Args:
        url: Webhook URL
        payload: Dict payload to send
        webhook_type: Type of webhook ('slack', 'discord', 'generic')

    Returns:
        True if successful, False otherwise
    """
    try:
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        request = Request(url, data=data, headers=headers, method="POST")
        response = urlopen(request, timeout=10)

        if response.status >= 200 and response.status < 300:
            logger.info(f"Webhook notification sent successfully to {webhook_type}")
            return True
        else:
            logger.warning(f"Webhook returned status {response.status}")
            return False

    except HTTPError as e:
        logger.error(f"Webhook HTTP error: {e.code} - {e.reason}")
        return False
    except URLError as e:
        logger.error(f"Webhook URL error: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return False


def notify_round_complete(round_number, stats=None):
    """Send notification when a round completes.

    Args:
        round_number: The completed round number
        stats: Optional dict with round statistics (passed, failed, total)
    """
    config = get_webhook_config()
    if not config or not config.get("on_round_complete"):
        return False

    url = config["url"]
    webhook_type = detect_webhook_type(url)

    title = f"Round {round_number} Complete"
    message = f"Round {round_number} has finished processing."

    fields = []
    if stats:
        if "passed" in stats:
            fields.append({"title": "Passed", "value": stats["passed"], "short": True})
        if "failed" in stats:
            fields.append({"title": "Failed", "value": stats["failed"], "short": True})
        if "total" in stats:
            fields.append(
                {"title": "Total Checks", "value": stats["total"], "short": True}
            )

    if webhook_type == "slack":
        payload = format_slack_message(
            title, message, color="good", fields=fields or None
        )
    elif webhook_type == "discord":
        payload = format_discord_message(
            title, message, color=0x00FF00, fields=fields or None
        )
    else:
        payload = format_generic_message(
            title, message, "round_complete", data={"round": round_number, "stats": stats}
        )

    return send_webhook(url, payload, webhook_type)


def notify_inject_graded(team_name, inject_title, score, max_score):
    """Send notification when an inject is graded.

    Args:
        team_name: Name of the team
        inject_title: Title of the inject
        score: Score received
        max_score: Maximum possible score
    """
    config = get_webhook_config()
    if not config or not config.get("on_inject_graded"):
        return False

    url = config["url"]
    webhook_type = detect_webhook_type(url)

    title = "Inject Graded"
    message = f"{team_name} received {score}/{max_score} on '{inject_title}'"

    fields = [
        {"title": "Team", "value": team_name, "short": True},
        {"title": "Score", "value": f"{score}/{max_score}", "short": True},
        {"title": "Inject", "value": inject_title, "short": False},
    ]

    # Color based on score percentage
    pct = (score / max_score * 100) if max_score > 0 else 0
    if pct >= 80:
        color = "good" if webhook_type == "slack" else 0x00FF00  # Green
    elif pct >= 50:
        color = "warning" if webhook_type == "slack" else 0xFFFF00  # Yellow
    else:
        color = "danger" if webhook_type == "slack" else 0xFF0000  # Red

    if webhook_type == "slack":
        payload = format_slack_message(title, message, color=color, fields=fields)
    elif webhook_type == "discord":
        payload = format_discord_message(title, message, color=color, fields=fields)
    else:
        payload = format_generic_message(
            title,
            message,
            "inject_graded",
            data={
                "team": team_name,
                "inject": inject_title,
                "score": score,
                "max_score": max_score,
            },
        )

    return send_webhook(url, payload, webhook_type)


def send_test_notification():
    """Send a test notification to verify webhook configuration.

    Returns:
        (success: bool, message: str)
    """
    config = get_webhook_config()
    if not config:
        return False, "Webhooks are not enabled or URL is not configured"

    url = config["url"]
    webhook_type = detect_webhook_type(url)

    title = "Test Notification"
    message = "This is a test notification from the Scoring Engine."

    if webhook_type == "slack":
        payload = format_slack_message(title, message, color="#439FE0")
    elif webhook_type == "discord":
        payload = format_discord_message(title, message, color=0x439FE0)
    else:
        payload = format_generic_message(title, message, "test")

    success = send_webhook(url, payload, webhook_type)

    if success:
        return True, f"Test notification sent successfully to {webhook_type} webhook"
    else:
        return False, "Failed to send test notification. Check the webhook URL and logs."
