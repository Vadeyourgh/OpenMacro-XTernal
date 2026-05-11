"""
OpenMacro XTernal - Python Edition
Global hotkey management.
"""

import keyboard
from typing import Callable, Dict


class HotkeyManager:
    """Manages global hotkey registration and change."""

    def __init__(self):
        self.active_hotkeys: Dict[str, Callable] = {}

    def register_all(self, hotkeys: dict, callbacks: dict):
        """Register all hotkeys from settings.

        Args:
            hotkeys: dict like {"start_macro": "F1", "fix_roblox": "F3", ...}
            callbacks: dict like {"start_macro": callable, "fix_roblox": callable, ...}
        """
        for action, key in hotkeys.items():
            if key and action in callbacks:
                self.register(key, callbacks[action])

    def register(self, key: str, callback: Callable):
        """Register a single hotkey."""
        if not key:
            return
        try:
            keyboard.add_hotkey(key, callback, suppress=False)
            self.active_hotkeys[key] = callback
        except Exception:
            pass

    def unregister(self, key: str):
        """Unregister a single hotkey."""
        if not key:
            return
        try:
            keyboard.remove_hotkey(key)
        except (KeyError, ValueError):
            pass
        self.active_hotkeys.pop(key, None)

    def change_hotkey(self, old_key: str, new_key: str, callback: Callable):
        """Change a hotkey binding."""
        if old_key == new_key:
            return
        self.unregister(old_key)
        self.register(new_key, callback)

    def unregister_all(self):
        """Remove all registered hotkeys."""
        for key in list(self.active_hotkeys.keys()):
            self.unregister(key)
        self.active_hotkeys.clear()
