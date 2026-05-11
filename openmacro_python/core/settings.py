"""
OpenMacro XTernal - Python Edition
Settings management: load, save, config profiles.
"""

import json
import os
import copy

from .constants import (
    APPDATA_DIR, CONFIGS_DIR, SETTINGS_PATH,
    get_default_settings, OBSOLETE_MAIN_SETTINGS, MIN_CAST_TIMEOUT_MS, FULL_VER,
)


def ensure_app_data_dirs():
    """Create appdata and config directories if needed."""
    os.makedirs(APPDATA_DIR, exist_ok=True)
    os.makedirs(CONFIGS_DIR, exist_ok=True)


def prune_obsolete_main_settings(main_settings: dict) -> bool:
    """Remove obsolete keys from main settings. Returns True if anything changed."""
    changed = False
    for key in OBSOLETE_MAIN_SETTINGS:
        if key in main_settings:
            del main_settings[key]
            changed = True
    return changed


def normalize_main_settings(main_settings: dict) -> bool:
    """Normalize and clamp main settings values. Returns True if anything changed."""
    changed = False

    if "cast_timeout_ms" in main_settings:
        try:
            val = int(main_settings["cast_timeout_ms"])
            normalized = max(MIN_CAST_TIMEOUT_MS, val)
            if normalized != main_settings["cast_timeout_ms"]:
                main_settings["cast_timeout_ms"] = normalized
                changed = True
        except (ValueError, TypeError):
            pass

    if "auto_appraise_mutation" in main_settings:
        val = str(main_settings["auto_appraise_mutation"]).strip()
        if val == "":
            val = "Mythical"
        if val != main_settings["auto_appraise_mutation"]:
            main_settings["auto_appraise_mutation"] = val
            changed = True

    for key in ["auto_appraise_click_x", "auto_appraise_click_y"]:
        if key not in main_settings:
            continue
        value = str(main_settings[key]).strip()
        try:
            normalized = round(float(value)) if value != "" else ""
        except (ValueError, TypeError):
            normalized = ""
        if normalized != main_settings[key]:
            main_settings[key] = normalized
            changed = True

    return changed


def load_settings() -> dict:
    """Load settings from disk or create defaults."""
    if not os.path.exists(SETTINGS_PATH):
        defaults = get_default_settings()
        _write_settings_file(SETTINGS_PATH, defaults)
        return defaults

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load settings: {e}")

    if "custom_theme" not in settings:
        settings["custom_theme"] = copy.deepcopy(settings.get("appearance", {}))

    if "last_migrated_version" not in settings:
        settings["last_migrated_version"] = ""

    # Fill missing main defaults
    default_main = get_default_settings()["main"]
    changed = False
    for key, val in default_main.items():
        if key not in settings.get("main", {}):
            settings.setdefault("main", {})[key] = val
            changed = True

    if prune_obsolete_main_settings(settings.get("main", {})):
        changed = True
    if normalize_main_settings(settings.get("main", {})):
        changed = True

    # Hotkey migration
    hotkeys = settings.get("hotkeys", {})
    if "stop_appraise" not in hotkeys:
        fix_key = hotkeys.get("fix_roblox", "F3")
        reload_key = hotkeys.get("reload", "F4")
        if fix_key == "F2":
            hotkeys["fix_roblox"] = "F3"
            if reload_key == "F3":
                hotkeys["reload"] = "F4"
        hotkeys["stop_appraise"] = "F2"
        changed = True

    if changed:
        _write_settings_file(SETTINGS_PATH, settings)

    return settings


def save_settings(settings: dict):
    """Save settings to disk."""
    _write_settings_file(SETTINGS_PATH, settings)


def _write_settings_file(path: str, data: dict):
    """Write settings JSON to disk."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def list_configs() -> list:
    """List saved config profile names."""
    if not os.path.isdir(CONFIGS_DIR):
        return []
    configs = []
    for fname in os.listdir(CONFIGS_DIR):
        if fname.endswith(".json"):
            configs.append(fname[:-5])
    return configs


def save_config(name: str, main_settings: dict):
    """Save a config profile."""
    data = copy.deepcopy(main_settings)
    prune_obsolete_main_settings(data)
    normalize_main_settings(data)
    path = os.path.join(CONFIGS_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_config(name: str) -> dict:
    """Load a config profile and return its main settings."""
    path = os.path.join(CONFIGS_DIR, f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_config(name: str):
    """Delete a config profile."""
    path = os.path.join(CONFIGS_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
