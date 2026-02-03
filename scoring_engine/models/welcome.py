import json

from scoring_engine.db import db
from scoring_engine.models.setting import Setting


def get_default_welcome_config():
    """Return the default welcome page configuration."""
    welcome_msg = (
        "<h2 class='text-center'>Welcome to the Competition!</h2>"
        "<p class='text-center'>Good luck to all teams.</p>"
    )
    return {
        "welcome_message": welcome_msg,
        "sponsor_tiers": [
            {"name": "Diamond", "display_order": 1, "sponsors": []},
            {"name": "Platinum", "display_order": 2, "sponsors": []},
            {"name": "Gold", "display_order": 3, "sponsors": []},
        ],
    }


def get_welcome_config():
    """
    Get the welcome page configuration from the database.
    Returns a dictionary with welcome_message and sponsor_tiers.
    """
    setting = Setting.get_setting("welcome_config")
    if setting is None:
        return get_default_welcome_config()

    try:
        config = json.loads(setting.value)
        # Validate structure
        if not isinstance(config, dict):
            return get_default_welcome_config()
        if "welcome_message" not in config:
            config["welcome_message"] = ""
        if "sponsor_tiers" not in config:
            config["sponsor_tiers"] = []
        return config
    except (json.JSONDecodeError, TypeError):
        return get_default_welcome_config()


def save_welcome_config(config):
    """
    Save the welcome page configuration to the database.
    Validates the structure before saving.
    """
    # Validate the config structure
    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")

    if "welcome_message" not in config:
        config["welcome_message"] = ""

    if "sponsor_tiers" not in config:
        config["sponsor_tiers"] = []

    # Validate sponsor tiers structure
    for tier in config.get("sponsor_tiers", []):
        if not isinstance(tier, dict):
            raise ValueError("Each sponsor tier must be a dictionary")
        if "name" not in tier:
            raise ValueError("Each sponsor tier must have a name")
        if "sponsors" not in tier:
            tier["sponsors"] = []
        if "display_order" not in tier:
            tier["display_order"] = 0

        # Validate sponsors in each tier
        for sponsor in tier.get("sponsors", []):
            if not isinstance(sponsor, dict):
                raise ValueError("Each sponsor must be a dictionary")
            if "name" not in sponsor:
                raise ValueError("Each sponsor must have a name")

    # Sort tiers by display_order
    config["sponsor_tiers"] = sorted(
        config["sponsor_tiers"], key=lambda x: x.get("display_order", 0)
    )

    # Get or create the setting
    setting = Setting.get_setting("welcome_config")
    if setting is None:
        setting = Setting(name="welcome_config", value=json.dumps(config))
        db.session.add(setting)
    else:
        setting.value = json.dumps(config)
        db.session.add(setting)

    db.session.commit()
    Setting.clear_cache("welcome_config")

    return config


def add_sponsor_tier(name, display_order=None):
    """Add a new sponsor tier."""
    config = get_welcome_config()

    if display_order is None:
        # Find the highest display_order and add 1
        orders = [t.get("display_order", 0) for t in config["sponsor_tiers"]]
        max_order = max(orders, default=0)
        display_order = max_order + 1

    new_tier = {"name": name, "display_order": display_order, "sponsors": []}

    config["sponsor_tiers"].append(new_tier)
    return save_welcome_config(config)


def remove_sponsor_tier(tier_name):
    """Remove a sponsor tier by name."""
    config = get_welcome_config()
    config["sponsor_tiers"] = [
        t for t in config["sponsor_tiers"] if t["name"] != tier_name
    ]
    return save_welcome_config(config)


def add_sponsor_to_tier(tier_name, sponsor_name, logo_url="", website=""):
    """Add a sponsor to a tier."""
    config = get_welcome_config()

    for tier in config["sponsor_tiers"]:
        if tier["name"] == tier_name:
            sponsor = {
                "name": sponsor_name,
                "logo_url": logo_url,
                "website": website,
            }
            tier["sponsors"].append(sponsor)
            break

    return save_welcome_config(config)


def remove_sponsor_from_tier(tier_name, sponsor_name):
    """Remove a sponsor from a tier."""
    config = get_welcome_config()

    for tier in config["sponsor_tiers"]:
        if tier["name"] == tier_name:
            tier["sponsors"] = [
                s for s in tier["sponsors"] if s["name"] != sponsor_name
            ]
            break

    return save_welcome_config(config)


def update_welcome_message(message):
    """Update the welcome message."""
    config = get_welcome_config()
    config["welcome_message"] = message
    return save_welcome_config(config)


def parse_welcome_from_yaml(yaml_config):
    """
    Parse welcome configuration from YAML competition config.

    Expected format:
    welcome:
      message: |
        <h2>Welcome!</h2>
        <p>Good luck to all teams.</p>
      sponsor_tiers:
        - name: Diamond
          sponsors:
            - name: Acme Corp
              logo: acme.png
              website: https://acme.com
        - name: Gold
          sponsors: []
    """
    if not yaml_config or not isinstance(yaml_config, dict):
        return None

    result = {
        "welcome_message": yaml_config.get("message", ""),
        "sponsor_tiers": [],
    }

    tiers = yaml_config.get("sponsor_tiers", [])
    for idx, tier in enumerate(tiers):
        if not isinstance(tier, dict):
            continue

        tier_data = {
            "name": tier.get("name", f"Tier {idx + 1}"),
            "display_order": idx + 1,
            "sponsors": [],
        }

        sponsors = tier.get("sponsors", [])
        if sponsors:
            for sponsor in sponsors:
                if isinstance(sponsor, dict):
                    logo = sponsor.get("logo", "")
                    # Convert relative logo paths to absolute static paths
                    if logo and not logo.startswith(("/", "http")):
                        logo = f"/static/images/sponsors/{logo}"
                    sponsor_data = {
                        "name": sponsor.get("name", ""),
                        "logo_url": logo,
                        "website": sponsor.get("website", ""),
                    }
                    tier_data["sponsors"].append(sponsor_data)

        result["sponsor_tiers"].append(tier_data)

    return result
