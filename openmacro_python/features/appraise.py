"""
OpenMacro XTernal - Python Edition
Auto-appraise system for fish mutation detection.
"""

import time
import re
import ctypes

from ..core.memory import GameMemory
from ..core.read import MemoryReader
from .fish import MacroState, release_mouse


APPRAISE_FIXED_DELAY_MS = 100


class AppraiseManager:
    """Handles the auto-appraise workflow."""

    def __init__(self, game: GameMemory, settings: dict):
        self.game = game
        self.settings = settings

    def is_enabled(self) -> bool:
        return bool(self.settings.get("auto_appraise_enabled", 0))

    def has_click_point(self) -> bool:
        x = self.settings.get("auto_appraise_click_x", "")
        y = self.settings.get("auto_appraise_click_y", "")
        try:
            if str(x).strip() and str(y).strip():
                float(x)
                float(y)
                return True
        except (ValueError, TypeError):
            pass
        return False

    def start_cycle(self, macro: MacroState) -> tuple:
        """Start an appraise cycle. Returns (success, message)."""
        if not self.game.is_anything_equipped():
            return False, "You must have a fish selected when appraising."

        if not self.has_click_point():
            return False, "Set a click point before appraising."

        mutation = str(self.settings.get("auto_appraise_mutation", "")).strip()
        if not mutation:
            return False, "Choose a desired mutation."

        release_mouse(macro)
        self._clear_cache(macro)

        macro.phase = "APPRAISE"
        macro.appraise_state = "RESOLVING"
        macro.cycle_enabled = True

        try:
            subvalues_addr = self._resolve_subvalues(macro)
            if not subvalues_addr:
                raise RuntimeError(
                    "Could not find fish info. Hold the fish before appraising."
                )

            macro.appraise_start_coins = self._read_coins()

            if self._has_desired_mutation(macro, mutation):
                macro.cycle_enabled = False
                macro.phase = "DONE"
                macro.appraise_state = "DONE"
                return True, f"{mutation} mutation was already present."

            macro.appraise_state = "CLICK_FIRST"
            return True, "Ready."

        except Exception as e:
            self._fail(macro, str(e))
            return False, str(e)

    def stop_cycle(self, macro: MacroState, message: str = "Stopped."):
        """Stop the appraise cycle."""
        release_mouse(macro)
        macro.cycle_enabled = False
        macro.phase = "OFF"
        self._clear_cache(macro)

    def update(self, macro: MacroState) -> str:
        """Update the appraise state machine. Returns status message."""
        now = time.time()
        elapsed_ms = (now - macro.appraise_last_click_at) * 1000 if macro.appraise_last_click_at else 9999

        if macro.appraise_state == "CLICK_FIRST":
            self._click_point()
            macro.appraise_last_click_at = now
            macro.appraise_state = "CLICK_SECOND"
            return "Clicking 1/2."

        elif macro.appraise_state == "CLICK_SECOND":
            if elapsed_ms < APPRAISE_FIXED_DELAY_MS:
                return "Clicking 1/2..."
            self._click_point()
            macro.appraise_last_click_at = now
            macro.appraise_wait_started_at = now
            macro.appraise_state = "WAIT_RESULT"
            return "Clicking 2/2."

        elif macro.appraise_state == "WAIT_RESULT":
            wait_elapsed = (now - macro.appraise_wait_started_at) * 1000
            if wait_elapsed < APPRAISE_FIXED_DELAY_MS:
                return "Waiting for result..."

            mutation = str(self.settings.get("auto_appraise_mutation", "")).strip()
            try:
                if self._has_desired_mutation(macro, mutation):
                    self._complete(macro, f"Found {mutation}.")
                    return f"Found {mutation}!"
            except Exception as e:
                self._fail(macro, str(e))
                return str(e)

            macro.appraise_wait_started_at = now
            macro.appraise_state = "WAIT_RETRY"
            return f"Still looking for {mutation}."

        elif macro.appraise_state == "WAIT_RETRY":
            wait_elapsed = (now - macro.appraise_wait_started_at) * 1000
            if wait_elapsed < APPRAISE_FIXED_DELAY_MS:
                return "Retrying..."
            macro.appraise_state = "CLICK_FIRST"
            return "Retrying."

        return ""

    def _resolve_subvalues(self, macro: MacroState) -> int:
        """Resolve the fishinfo/Info/Subvalues instance."""
        workspace = self.game.get_workspace()
        if not workspace:
            return 0
        lp = self.game.get_local_player()
        if not lp:
            return 0
        player_name = self.game.reader.read_instance_name(lp)
        if not player_name or player_name == "<null>":
            return 0
        character = self.game.reader.find_child_by_name(workspace, player_name)
        if not character:
            return 0
        fishinfo = self.game.reader.find_child_by_name(character, "fishinfo")
        if not fishinfo:
            return 0
        info = self.game.reader.find_child_by_name(fishinfo, "Info")
        if not info:
            return 0
        subvalues = self.game.reader.find_child_by_name(info, "Subvalues")
        if subvalues:
            macro.appraise_subvalues_addr = subvalues
        return subvalues

    def _has_desired_mutation(self, macro: MacroState, desired: str) -> bool:
        """Check if the desired mutation exists in the cached subvalues."""
        subvalues = self._resolve_subvalues(macro)
        if not subvalues:
            raise RuntimeError("Could not find subvalues. Hold or re-equip the fish.")

        desired_lower = self._normalize(desired)
        if not desired_lower:
            return False

        haystack = self._collect_text(subvalues)
        return desired_lower in self._normalize(haystack)

    def _collect_text(self, addr: int) -> str:
        """Collect all text from subvalues tree."""
        parts = []
        self._append_text(parts, addr)
        for child in self.game.reader.read_children(addr):
            self._append_text(parts, child)
            for desc in self.game.reader.read_children(child):
                self._append_text(parts, desc)
        return " ".join(parts)

    def _append_text(self, parts: list, addr: int):
        try:
            cls = self.game.reader.read_class_name(addr)
            if "Text" not in cls and "Value" not in cls:
                return
            text = self.game.reader.read_gui_text(addr)
            text = text.strip()
            if text:
                parts.append(text)
        except Exception:
            pass

    def _normalize(self, text: str) -> str:
        text = text.replace("\r", "\n")
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.lower().strip()

    def _click_point(self):
        """Click at the configured appraise point."""
        x = int(round(float(self.settings.get("auto_appraise_click_x", 0))))
        y = int(round(float(self.settings.get("auto_appraise_click_y", 0))))

        # Move cursor and click
        ctypes.windll.user32.SetCursorPos(x, y)
        time.sleep(0.015)
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # down
        time.sleep(0.01)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # up

    def _read_coins(self) -> str:
        """Read current coin count from GUI."""
        pg = self.game.get_player_gui()
        if not pg:
            return ""
        hud = self.game.reader.find_child_by_name(pg, "hud")
        if not hud:
            return ""
        safezone = self.game.reader.find_child_by_name(hud, "safezone")
        if not safezone:
            return ""
        coins = self.game.reader.find_child_by_name(safezone, "coins")
        if not coins:
            return ""
        text = self.game.reader.read_gui_text(coins)
        digits = re.sub(r"\D", "", text)
        return digits if digits else ""

    def _complete(self, macro: MacroState, message: str):
        macro.appraise_end_coins = self._read_coins()
        macro.cycle_enabled = False
        macro.appraise_state = "DONE"
        macro.phase = "DONE"

    def _fail(self, macro: MacroState, message: str):
        macro.appraise_end_coins = self._read_coins()
        macro.cycle_enabled = False
        macro.appraise_state = "FAILED"
        macro.appraise_last_error = message
        macro.phase = "FAILED"

    def _clear_cache(self, macro: MacroState):
        macro.appraise_subvalues_addr = 0
        macro.appraise_last_click_at = 0
        macro.appraise_wait_started_at = 0
        macro.appraise_start_coins = ""
        macro.appraise_end_coins = ""
        macro.appraise_state = "IDLE"
        macro.appraise_last_error = ""
