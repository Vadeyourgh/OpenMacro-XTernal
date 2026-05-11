"""
OpenMacro XTernal - Python Edition
Global hotkey management using pynput (no admin required).
"""

from pynput import keyboard as pynput_kb
from typing import Callable, Dict, Optional
import threading


# Map common key names to pynput Key objects
_SPECIAL_KEYS = {
    "F1": pynput_kb.Key.f1,
    "F2": pynput_kb.Key.f2,
    "F3": pynput_kb.Key.f3,
    "F4": pynput_kb.Key.f4,
    "F5": pynput_kb.Key.f5,
    "F6": pynput_kb.Key.f6,
    "F7": pynput_kb.Key.f7,
    "F8": pynput_kb.Key.f8,
    "F9": pynput_kb.Key.f9,
    "F10": pynput_kb.Key.f10,
    "F11": pynput_kb.Key.f11,
    "F12": pynput_kb.Key.f12,
    "ESC": pynput_kb.Key.esc,
    "ESCAPE": pynput_kb.Key.esc,
    "SPACE": pynput_kb.Key.space,
    "ENTER": pynput_kb.Key.enter,
    "TAB": pynput_kb.Key.tab,
    "HOME": pynput_kb.Key.home,
    "END": pynput_kb.Key.end,
    "INSERT": pynput_kb.Key.insert,
    "DELETE": pynput_kb.Key.delete,
    "PAGEUP": pynput_kb.Key.page_up,
    "PAGEDOWN": pynput_kb.Key.page_down,
}


def _normalize_key_name(key_str: str) -> str:
    """Normalize a key name to uppercase for comparison."""
    return key_str.strip().upper()


class HotkeyManager:
    """Manages global hotkey registration using pynput listener."""

    def __init__(self):
        self.active_hotkeys: Dict[str, Callable] = {}
        self._listener: Optional[pynput_kb.Listener] = None
        self._lock = threading.Lock()

    def register_all(self, hotkeys: dict, callbacks: dict):
        """Register all hotkeys from settings.

        Args:
            hotkeys: dict like {"start_macro": "F1", "fix_roblox": "F3", ...}
            callbacks: dict like {"start_macro": callable, "fix_roblox": callable, ...}
        """
        for action, key in hotkeys.items():
            if key and action in callbacks:
                self.register(key, callbacks[action])

        # Start the listener after registering all hotkeys
        self._start_listener()

    def register(self, key: str, callback: Callable):
        """Register a single hotkey."""
        if not key:
            return
        normalized = _normalize_key_name(key)
        with self._lock:
            self.active_hotkeys[normalized] = callback

    def unregister(self, key: str):
        """Unregister a single hotkey."""
        if not key:
            return
        normalized = _normalize_key_name(key)
        with self._lock:
            self.active_hotkeys.pop(normalized, None)

    def change_hotkey(self, old_key: str, new_key: str, callback: Callable):
        """Change a hotkey binding."""
        if old_key == new_key:
            return
        self.unregister(old_key)
        self.register(new_key, callback)

    def unregister_all(self):
        """Remove all registered hotkeys and stop listener."""
        with self._lock:
            self.active_hotkeys.clear()
        self._stop_listener()

    def _start_listener(self):
        """Start the pynput keyboard listener."""
        if self._listener is not None:
            return

        self._listener = pynput_kb.Listener(on_press=self._on_key_press)
        self._listener.daemon = True
        self._listener.start()

    def _stop_listener(self):
        """Stop the pynput keyboard listener."""
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_key_press(self, key):
        """Handle a key press event from pynput."""
        key_name = self._key_to_name(key)
        if not key_name:
            return

        with self._lock:
            callback = self.active_hotkeys.get(key_name)

        if callback:
            # Run callback in a separate thread to avoid blocking the listener
            threading.Thread(target=callback, daemon=True).start()

    def _key_to_name(self, key) -> str:
        """Convert a pynput key to a normalized name string."""
        # Special keys (F1-F12, Esc, etc.)
        if isinstance(key, pynput_kb.Key):
            for name, pynput_key in _SPECIAL_KEYS.items():
                if key == pynput_key:
                    return name
            # Try the key's name attribute
            try:
                return key.name.upper()
            except AttributeError:
                return ""

        # Regular character keys
        if hasattr(key, "char") and key.char:
            return key.char.upper()

        # Virtual key code (e.g. for keys like numpad)
        if hasattr(key, "vk") and key.vk:
            # F1-F12 via vk codes (112-123)
            if 112 <= key.vk <= 123:
                return f"F{key.vk - 111}"
            return ""

        return ""
