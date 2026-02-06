from flask import Blueprint, render_template

from scoring_engine.models.setting import Setting
from scoring_engine.models.welcome import get_welcome_config

mod = Blueprint('welcome', __name__)


@mod.route('/')
@mod.route("/index")
def home():
    # Try structured welcome config first
    welcome_config = get_welcome_config()

    # Check if structured config has any real content
    has_message = bool(
        welcome_config.get("welcome_message", "").strip()
    )
    has_sponsors = any(
        len(tier.get("sponsors", [])) > 0
        for tier in welcome_config.get("sponsor_tiers", [])
    )

    # If structured config has content, use it
    if has_message or has_sponsors:
        return render_template(
            'welcome.html',
            welcome_config=welcome_config,
            use_legacy=False,
        )

    # Fall back to legacy welcome_page_content
    legacy_setting = Setting.get_setting('welcome_page_content')
    if legacy_setting and legacy_setting.value.strip():
        return render_template(
            'welcome.html',
            welcome_content=legacy_setting.value,
            use_legacy=True,
        )

    # No content at all - use structured mode with defaults
    return render_template(
        'welcome.html',
        welcome_config=welcome_config,
        use_legacy=False,
    )
