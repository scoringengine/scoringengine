"""Tests for welcome page configuration model."""

import json

import pytest

from scoring_engine.db import db
from scoring_engine.models.setting import Setting
from scoring_engine.models.welcome import (
    add_sponsor_tier,
    add_sponsor_to_tier,
    get_default_welcome_config,
    get_welcome_config,
    parse_welcome_from_yaml,
    remove_sponsor_from_tier,
    remove_sponsor_tier,
    save_welcome_config,
    update_welcome_message,
)


class TestGetDefaultWelcomeConfig:
    def test_returns_dict_with_expected_keys(self):
        config = get_default_welcome_config()
        assert "welcome_message" in config
        assert "sponsor_tiers" in config

    def test_has_three_default_tiers(self):
        config = get_default_welcome_config()
        assert len(config["sponsor_tiers"]) == 3
        names = [t["name"] for t in config["sponsor_tiers"]]
        assert names == ["Diamond", "Platinum", "Gold"]

    def test_tiers_have_empty_sponsors(self):
        config = get_default_welcome_config()
        for tier in config["sponsor_tiers"]:
            assert tier["sponsors"] == []
            assert "display_order" in tier


class TestGetWelcomeConfig:
    def test_returns_default_when_no_setting(self):
        config = get_welcome_config()
        default = get_default_welcome_config()
        assert config == default

    def test_returns_saved_config(self):
        saved = {"welcome_message": "Hello!", "sponsor_tiers": []}
        setting = Setting(name="welcome_config", value=json.dumps(saved))
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("welcome_config")

        config = get_welcome_config()
        assert config["welcome_message"] == "Hello!"
        assert config["sponsor_tiers"] == []

    def test_returns_default_on_corrupt_json(self):
        setting = Setting(name="welcome_config", value="not valid json{{{")
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("welcome_config")

        config = get_welcome_config()
        default = get_default_welcome_config()
        assert config == default

    def test_returns_default_on_non_dict_json(self):
        setting = Setting(name="welcome_config", value=json.dumps([1, 2, 3]))
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("welcome_config")

        config = get_welcome_config()
        default = get_default_welcome_config()
        assert config == default

    def test_adds_missing_welcome_message(self):
        saved = {"sponsor_tiers": [{"name": "Gold", "display_order": 1, "sponsors": []}]}
        setting = Setting(name="welcome_config", value=json.dumps(saved))
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("welcome_config")

        config = get_welcome_config()
        assert config["welcome_message"] == ""
        assert len(config["sponsor_tiers"]) == 1

    def test_adds_missing_sponsor_tiers(self):
        saved = {"welcome_message": "Hi"}
        setting = Setting(name="welcome_config", value=json.dumps(saved))
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("welcome_config")

        config = get_welcome_config()
        assert config["sponsor_tiers"] == []


class TestSaveWelcomeConfig:
    def test_saves_valid_config(self):
        config = {
            "welcome_message": "Test",
            "sponsor_tiers": [
                {"name": "Gold", "display_order": 1, "sponsors": []},
            ],
        }
        result = save_welcome_config(config)
        assert result["welcome_message"] == "Test"

        setting = Setting.get_setting("welcome_config")
        assert setting is not None
        saved = json.loads(setting.value)
        assert saved["welcome_message"] == "Test"

    def test_raises_on_non_dict(self):
        with pytest.raises(ValueError, match="must be a dictionary"):
            save_welcome_config("not a dict")

    def test_raises_on_non_dict_tier(self):
        config = {"welcome_message": "", "sponsor_tiers": ["not a dict"]}
        with pytest.raises(ValueError, match="tier must be a dictionary"):
            save_welcome_config(config)

    def test_raises_on_tier_missing_name(self):
        config = {"welcome_message": "", "sponsor_tiers": [{"sponsors": []}]}
        with pytest.raises(ValueError, match="must have a name"):
            save_welcome_config(config)

    def test_raises_on_non_dict_sponsor(self):
        config = {
            "welcome_message": "",
            "sponsor_tiers": [{"name": "Gold", "sponsors": ["bad"]}],
        }
        with pytest.raises(ValueError, match="sponsor must be a dictionary"):
            save_welcome_config(config)

    def test_raises_on_sponsor_missing_name(self):
        config = {
            "welcome_message": "",
            "sponsor_tiers": [{"name": "Gold", "sponsors": [{"logo_url": "x"}]}],
        }
        with pytest.raises(ValueError, match="sponsor must have a name"):
            save_welcome_config(config)

    def test_sorts_tiers_by_display_order(self):
        config = {
            "welcome_message": "",
            "sponsor_tiers": [
                {"name": "Bronze", "display_order": 3, "sponsors": []},
                {"name": "Gold", "display_order": 1, "sponsors": []},
                {"name": "Silver", "display_order": 2, "sponsors": []},
            ],
        }
        result = save_welcome_config(config)
        names = [t["name"] for t in result["sponsor_tiers"]]
        assert names == ["Gold", "Silver", "Bronze"]

    def test_adds_missing_welcome_message(self):
        config = {"sponsor_tiers": []}
        result = save_welcome_config(config)
        assert result["welcome_message"] == ""

    def test_adds_missing_sponsor_tiers(self):
        config = {"welcome_message": "Hi"}
        result = save_welcome_config(config)
        assert result["sponsor_tiers"] == []

    def test_adds_default_display_order(self):
        config = {
            "welcome_message": "",
            "sponsor_tiers": [{"name": "Gold", "sponsors": []}],
        }
        result = save_welcome_config(config)
        assert result["sponsor_tiers"][0]["display_order"] == 0

    def test_adds_missing_sponsors_list(self):
        config = {
            "welcome_message": "",
            "sponsor_tiers": [{"name": "Gold", "display_order": 1}],
        }
        result = save_welcome_config(config)
        assert result["sponsor_tiers"][0]["sponsors"] == []

    def test_updates_existing_setting(self):
        config1 = {"welcome_message": "First", "sponsor_tiers": []}
        save_welcome_config(config1)

        config2 = {"welcome_message": "Second", "sponsor_tiers": []}
        save_welcome_config(config2)

        setting = Setting.get_setting("welcome_config")
        saved = json.loads(setting.value)
        assert saved["welcome_message"] == "Second"


class TestAddSponsorTier:
    def test_adds_tier_with_explicit_order(self):
        result = add_sponsor_tier("Silver", display_order=5)
        tier_names = [t["name"] for t in result["sponsor_tiers"]]
        assert "Silver" in tier_names

    def test_auto_increments_display_order(self):
        result = add_sponsor_tier("Custom")
        custom = [t for t in result["sponsor_tiers"] if t["name"] == "Custom"][0]
        # Default tiers have orders 1, 2, 3 so custom should be 4
        assert custom["display_order"] == 4


class TestRemoveSponsorTier:
    def test_removes_existing_tier(self):
        result = remove_sponsor_tier("Gold")
        tier_names = [t["name"] for t in result["sponsor_tiers"]]
        assert "Gold" not in tier_names
        assert "Diamond" in tier_names
        assert "Platinum" in tier_names

    def test_no_error_removing_nonexistent_tier(self):
        result = remove_sponsor_tier("Nonexistent")
        assert len(result["sponsor_tiers"]) == 3


class TestAddSponsorToTier:
    def test_adds_sponsor_to_existing_tier(self):
        result = add_sponsor_to_tier("Gold", "Acme Corp", logo_url="/img/acme.png", website="https://acme.com")
        gold = [t for t in result["sponsor_tiers"] if t["name"] == "Gold"][0]
        assert len(gold["sponsors"]) == 1
        assert gold["sponsors"][0]["name"] == "Acme Corp"
        assert gold["sponsors"][0]["logo_url"] == "/img/acme.png"
        assert gold["sponsors"][0]["website"] == "https://acme.com"

    def test_adds_sponsor_with_defaults(self):
        result = add_sponsor_to_tier("Gold", "Simple Corp")
        gold = [t for t in result["sponsor_tiers"] if t["name"] == "Gold"][0]
        assert gold["sponsors"][0]["logo_url"] == ""
        assert gold["sponsors"][0]["website"] == ""


class TestRemoveSponsorFromTier:
    def test_removes_sponsor(self):
        add_sponsor_to_tier("Gold", "Acme Corp")
        add_sponsor_to_tier("Gold", "Other Corp")
        result = remove_sponsor_from_tier("Gold", "Acme Corp")
        gold = [t for t in result["sponsor_tiers"] if t["name"] == "Gold"][0]
        assert len(gold["sponsors"]) == 1
        assert gold["sponsors"][0]["name"] == "Other Corp"


class TestUpdateWelcomeMessage:
    def test_updates_message(self):
        result = update_welcome_message("<h1>New Message</h1>")
        assert result["welcome_message"] == "<h1>New Message</h1>"

        config = get_welcome_config()
        assert config["welcome_message"] == "<h1>New Message</h1>"


class TestParseWelcomeFromYaml:
    def test_returns_none_for_none(self):
        assert parse_welcome_from_yaml(None) is None

    def test_returns_none_for_non_dict(self):
        assert parse_welcome_from_yaml("string") is None

    def test_returns_none_for_empty_dict(self):
        # Empty dict is falsy, so parse_welcome_from_yaml returns None
        assert parse_welcome_from_yaml({}) is None

    def test_parses_message(self):
        yaml_config = {"message": "<h2>Welcome!</h2>"}
        result = parse_welcome_from_yaml(yaml_config)
        assert result["welcome_message"] == "<h2>Welcome!</h2>"

    def test_parses_sponsor_tiers(self):
        yaml_config = {
            "message": "Hello",
            "sponsor_tiers": [
                {
                    "name": "Diamond",
                    "sponsors": [
                        {"name": "Acme", "logo": "acme.png", "website": "https://acme.com"},
                    ],
                },
                {"name": "Gold", "sponsors": []},
            ],
        }
        result = parse_welcome_from_yaml(yaml_config)
        assert len(result["sponsor_tiers"]) == 2
        assert result["sponsor_tiers"][0]["name"] == "Diamond"
        assert result["sponsor_tiers"][0]["display_order"] == 1
        assert result["sponsor_tiers"][1]["name"] == "Gold"
        assert result["sponsor_tiers"][1]["display_order"] == 2

    def test_converts_relative_logo_paths(self):
        yaml_config = {
            "sponsor_tiers": [
                {
                    "name": "Gold",
                    "sponsors": [{"name": "Acme", "logo": "acme.png"}],
                },
            ],
        }
        result = parse_welcome_from_yaml(yaml_config)
        sponsor = result["sponsor_tiers"][0]["sponsors"][0]
        assert sponsor["logo_url"] == "/static/images/sponsors/acme.png"

    def test_preserves_absolute_logo_paths(self):
        yaml_config = {
            "sponsor_tiers": [
                {
                    "name": "Gold",
                    "sponsors": [{"name": "Acme", "logo": "/custom/path/acme.png"}],
                },
            ],
        }
        result = parse_welcome_from_yaml(yaml_config)
        sponsor = result["sponsor_tiers"][0]["sponsors"][0]
        assert sponsor["logo_url"] == "/custom/path/acme.png"

    def test_preserves_http_logo_urls(self):
        yaml_config = {
            "sponsor_tiers": [
                {
                    "name": "Gold",
                    "sponsors": [{"name": "Acme", "logo": "https://example.com/logo.png"}],
                },
            ],
        }
        result = parse_welcome_from_yaml(yaml_config)
        sponsor = result["sponsor_tiers"][0]["sponsors"][0]
        assert sponsor["logo_url"] == "https://example.com/logo.png"

    def test_skips_non_dict_tiers(self):
        yaml_config = {
            "sponsor_tiers": ["not a dict", {"name": "Gold", "sponsors": []}],
        }
        result = parse_welcome_from_yaml(yaml_config)
        assert len(result["sponsor_tiers"]) == 1
        assert result["sponsor_tiers"][0]["name"] == "Gold"

    def test_skips_non_dict_sponsors(self):
        yaml_config = {
            "sponsor_tiers": [
                {"name": "Gold", "sponsors": ["not a dict", {"name": "Acme"}]},
            ],
        }
        result = parse_welcome_from_yaml(yaml_config)
        assert len(result["sponsor_tiers"][0]["sponsors"]) == 1
        assert result["sponsor_tiers"][0]["sponsors"][0]["name"] == "Acme"

    def test_default_tier_name_when_missing(self):
        yaml_config = {
            "sponsor_tiers": [{"sponsors": []}],
        }
        result = parse_welcome_from_yaml(yaml_config)
        assert result["sponsor_tiers"][0]["name"] == "Tier 1"

    def test_empty_logo_url(self):
        yaml_config = {
            "sponsor_tiers": [
                {"name": "Gold", "sponsors": [{"name": "Acme"}]},
            ],
        }
        result = parse_welcome_from_yaml(yaml_config)
        assert result["sponsor_tiers"][0]["sponsors"][0]["logo_url"] == ""
