"""
OpenMacro XTernal - Python Edition
Constants and default configuration values.
"""

import os

MAJOR_VER = "v0"
FULL_VER = "v0.2.20"
ROBLOX_VER = "version-bf6344c9c23446bf"

GITHUB_OWNER = "termx3"
GITHUB_REPO = "OpenMacro-XTernal"
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/version.txt"
TAG_ZIP_BASE_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/refs/tags/"

ROBLOX_PROCESS_NAME = "RobloxPlayerBeta.exe"

APPDATA_DIR = os.path.join(os.getenv("APPDATA", ""), "OpenMacro", "XTernal")
CONFIGS_DIR = os.path.join(APPDATA_DIR, "configs")
SETTINGS_PATH = os.path.join(APPDATA_DIR, "settings.json")
OFFSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "settings", "offsets.json")

# Known rod names
KNOWN_ROD_NAMES = [
    "Pinion's Aria",
    "Tranquility Rod",
    "Rod Of The Eternal King",
    "Rod Of The Depths",
    "Rod Of Time",
    "Flimsy Rod",
    "Training Rod",
    "Plastic Rod",
    "Steady Rod",
    "Reinforced Rod",
    "Phoenix Rod",
    "Mythical Rod",
    "No-Life Rod",
    "Sunken Rod",
    "Trident Rod",
    "Kings Rod",
    "Wisdom Rod",
    "Toxinburst Rod",
    "The Lost Rod",
    "Riptide Rod",
    "Lucid Rod",
    "Celestial Rod",
    "Seasons Rod",
    "Krampus's Rod",
    "Precision Rod",
    "Resourceful Rod",
    "Toxic Spire Rod",
    "Gardenkeeper Rod",
    "Voyager Rod",
    "Vineweaver Rod",
]

# Supported mutations
MUTATIONS = [
    "Mythical", "Abyssal", "Glossy", "Electric", "Negative",
    "Amber", "Fossilized", "Silver", "Darkened", "Scorched",
    "Albino", "Lunar", "Mosaic", "Translucent", "Shiny",
    "Big", "Midas", "Hexed", "Frozen", "Sparkling",
]

# Built-in themes
BUILT_IN_THEMES = {
    "Default": {
        "accent_color": "5aa9ff",
        "bg_color": "0f1115",
        "text_color": "f5f7fa",
        "border_color": "2a2f3a",
    },
    "Crimson": {
        "accent_color": "ff4c4c",
        "bg_color": "1a0a0a",
        "text_color": "f5e6e6",
        "border_color": "3a1f1f",
    },
    "Emerald": {
        "accent_color": "3ddfa0",
        "bg_color": "0a1512",
        "text_color": "e6f5ef",
        "border_color": "1f3a2d",
    },
    "Amber": {
        "accent_color": "ffb347",
        "bg_color": "15120a",
        "text_color": "f5f0e6",
        "border_color": "3a331f",
    },
    "Lavender": {
        "accent_color": "b388ff",
        "bg_color": "120e18",
        "text_color": "ede6f5",
        "border_color": "2d1f3a",
    },
    "Arctic": {
        "accent_color": "88cfff",
        "bg_color": "e8edf2",
        "text_color": "1a1e24",
        "border_color": "c0c8d4",
    },
    "Slate": {
        "accent_color": "78909c",
        "bg_color": "1e272e",
        "text_color": "cfd8dc",
        "border_color": "37474f",
    },
}


def get_default_settings():
    """Return a fresh copy of default settings."""
    return {
        "appearance": {
            "accent_color": "5aa9ff",
            "bg_color": "0f1115",
            "text_color": "f5f7fa",
            "border_color": "2a2f3a",
        },
        "env": "prod",
        "hotkeys": {
            "start_macro": "F1",
            "stop_appraise": "F2",
            "fix_roblox": "F3",
            "reload": "F4",
        },
        "main": {
            "derivative_gain": 0.55,
            "edge_boundary": 0.1,
            "neutral_duty_cycle": 0.5,
            "prediction_strength": 7.5,
            "proportional_gain": 0.42,
            "resilience": 0.0,
            "update_rate": 21,
            "velocity_damping": 38,
            "cast_mode": "short",
            "cast_power_custom": 96.0,
            "cast_timeout_ms": 15000,
            "pre_cast_delay_ms": 0,
            "post_cast_delay_ms": 150,
            "cast_on_timeout": 1,
            "fishing_action_delay_ms": 0,
            "completion_threshold": 99.7,
            "shake_interval_ms": 25,
            "auto_appraise_mutation": "Mythical",
            "auto_appraise_click_x": "",
            "auto_appraise_click_y": "",
            "auto_totem_enabled": 0,
            "auto_totem_name": "Aurora Totem",
            "auto_totem_mode": "expire",
            "auto_totem_interval_sec": 900,
            "webhook_url": "",
            "webhook_enabled": 0,
            "webhook_summary_interval_min": 30,
            "webhook_summary_fish": 1,
            "webhook_summary_success_rate": 1,
            "webhook_summary_rod": 1,
            "webhook_summary_config": 1,
            "webhook_summary_totem_state": 1,
            "webhook_summary_totem_pops": 1,
            "webhook_summary_session_time": 1,
            "webhook_summary_cast_timeouts": 1,
            "webhook_alert_totem_failed": 1,
        },
        "last_config": "",
        "last_migrated_version": "",
        "last_theme": "Default",
        "custom_theme": {
            "accent_color": "5aa9ff",
            "bg_color": "0f1115",
            "text_color": "f5f7fa",
            "border_color": "2a2f3a",
        },
        "update": {
            "auto_update": 0,
            "show_confirmation": 1,
        },
    }


# Obsolete settings to prune
OBSOLETE_MAIN_SETTINGS = [
    "close_threshold",
    "fishing_end_grace_ms",
    "post_catch_delay_ms",
    "post_totem_delay_ms",
    "auto_appraise_max_cash",
    "auto_appraise_click_delay_ms",
    "auto_appraise_check_delay_ms",
    "auto_appraise_retry_delay_ms",
    "auto_appraise_enabled",
]

MIN_CAST_TIMEOUT_MS = 5000
