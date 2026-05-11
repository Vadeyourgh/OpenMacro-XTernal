"""
OpenMacro XTernal - Python Edition
Auto-totem system for Aurora Totem automation.
"""

import time
import keyboard

from ..core.memory import GameMemory
from .fish import MacroState, release_mouse


AUTO_TOTEM_WAIT_MS = 30000


class TotemManager:
    """Manages the auto-totem workflow (Aurora + Sundial cycle)."""

    def __init__(self, game: GameMemory, settings: dict):
        self.game = game
        self.settings = settings

    def is_enabled(self) -> bool:
        main = self.settings
        return bool(main.get("auto_totem_enabled", 0)) and (
            main.get("auto_totem_name", "") == "Aurora Totem"
        )

    def get_interval_ms(self) -> int:
        return max(1, int(self.settings.get("auto_totem_interval_sec", 900))) * 1000

    def is_due(self, macro: MacroState) -> bool:
        """Check if an auto-totem cycle is due."""
        if not self.is_enabled():
            return False

        main = self.settings
        mode = main.get("auto_totem_mode", "expire")

        if mode == "interval":
            reference = macro.last_totem_success_at
            if macro.last_totem_attempt_at > reference:
                reference = macro.last_totem_attempt_at
            if not reference:
                return True
            elapsed_ms = (time.time() - reference) * 1000
            return elapsed_ms >= self.get_interval_ms()

        # "expire" mode
        if macro.totem_night_covered:
            cycle_text = self.game.get_world_status_text("4_cycle").lower()
            if cycle_text == "" or "night" in cycle_text:
                return False
            macro.totem_night_covered = False

        return True

    def is_safe_boundary(self, macro: MacroState) -> bool:
        """Check if we're at a safe point to interrupt for totem use."""
        return (
            macro.phase == "CASTING"
            and not macro.is_holding
            and not macro.cast_bar_seen
        )

    def begin_workflow(self, macro: MacroState):
        """Start the auto-totem workflow."""
        macro.totem_pending = False
        macro.totem_retry_count = 0
        macro.totem_wait_started_at = 0
        macro.last_totem_attempt_at = time.time()
        macro.totem_needs_rod_reequip = False

        release_mouse(macro)

        if macro.totem_needs_settle_delay:
            macro.totem_state = "TOTEM_SETTLE"
            macro.totem_wait_started_at = time.time()
            return

        self._run_step(macro)

    def _run_step(self, macro: MacroState):
        """Execute the main totem decision logic."""
        if self.game.is_aurora_active():
            self._complete(macro, success=True)
            return

        if self.game.is_night_cycle():
            if not self._try_use_item("Aurora Totem", macro):
                self._complete(macro, success=False)
                return
            macro.totem_state = "TOTEM_WAIT_AURORA"
            macro.totem_wait_started_at = time.time()
            return

        # Not night - use sundial
        if not self._try_use_item("Sundial Totem", macro):
            self._complete(macro, success=False)
            return

        macro.totem_state = "TOTEM_WAIT_NIGHT"
        macro.totem_wait_started_at = time.time()

    def update_state(self, macro: MacroState):
        """Update the totem state machine each tick."""
        if self.game.is_aurora_active():
            self._complete(macro, success=True)
            return

        elapsed_ms = (time.time() - macro.totem_wait_started_at) * 1000

        if macro.totem_state == "TOTEM_SETTLE":
            delay = max(0, int(self.settings.get("pre_cast_delay_ms", 0)))
            if elapsed_ms < delay:
                return
            macro.totem_needs_settle_delay = False
            macro.totem_wait_started_at = 0
            self._run_step(macro)

        elif macro.totem_state == "TOTEM_WAIT_NIGHT":
            if self.game.is_night_cycle():
                macro.totem_retry_count = 0
                if not self._try_use_item("Aurora Totem", macro):
                    self._complete(macro, success=False)
                    return
                macro.totem_state = "TOTEM_WAIT_AURORA"
                macro.totem_wait_started_at = time.time()
                return

            if elapsed_ms >= AUTO_TOTEM_WAIT_MS:
                if macro.totem_retry_count >= 1:
                    self._complete(macro, success=False)
                    return
                if not self._try_use_item("Sundial Totem", macro):
                    self._complete(macro, success=False)
                    return
                macro.totem_retry_count += 1
                macro.totem_wait_started_at = time.time()

        elif macro.totem_state == "TOTEM_WAIT_AURORA":
            if elapsed_ms >= AUTO_TOTEM_WAIT_MS:
                if macro.totem_retry_count >= 1:
                    self._complete(macro, success=False)
                    return
                if not self._try_use_item("Aurora Totem", macro):
                    self._complete(macro, success=False)
                    return
                macro.totem_retry_count += 1
                macro.totem_wait_started_at = time.time()

    def _try_use_item(self, item_name: str, macro: MacroState) -> bool:
        """Simulate using a hotbar item by pressing its slot key."""
        slot_key = self._get_item_slot_key(item_name)
        if not slot_key:
            return False

        keyboard.press_and_release(slot_key)
        time.sleep(0.175)
        keyboard.press_and_release("space")  # click equivalent
        time.sleep(0.1)

        macro.totem_needs_rod_reequip = True
        return True

    def _get_item_slot_key(self, item_name: str) -> str:
        """Find the hotbar slot key for a given item."""
        hotbar = self.game.get_hotbar_gui()
        if not hotbar:
            return ""

        for item_addr in self.game.reader.read_children(hotbar):
            if self.game.reader.read_class_name(item_addr) != "ImageButton":
                continue
            if self.game.reader.read_instance_name(item_addr) != "ItemTemplate":
                continue

            name_inst = self.game.reader.find_child_by_name(item_addr, "ItemName")
            if not name_inst:
                continue

            text = self.game.reader.normalize_text(self.game.reader.read_gui_text(name_inst))
            if text != item_name:
                continue

            # Find the slot key text label
            for child in self.game.reader.read_children(item_addr):
                cls = self.game.reader.read_class_name(child)
                name = self.game.reader.read_instance_name(child)
                if cls == "TextLabel" and name == "TextLabel":
                    key_text = self.game.reader.normalize_text(
                        self.game.reader.read_gui_text(child)
                    )
                    return key_text

        return ""

    def _complete(self, macro: MacroState, success: bool):
        """Complete the totem workflow."""
        if success:
            macro.last_totem_success_at = time.time()
            macro.totem_night_covered = True
            macro.totem_pop_count += 1

        self._reset_control(macro)

        if macro.totem_needs_rod_reequip:
            keyboard.press_and_release("1")
            time.sleep(0.075)

        if not success and self.settings.get("auto_totem_mode") == "expire":
            macro.totem_blocked_until_catch_end = True

    def _reset_control(self, macro: MacroState):
        """Reset totem control state."""
        macro.totem_state = "IDLE"
        macro.totem_retry_count = 0
        macro.totem_wait_started_at = 0
        macro.totem_pending = False
        macro.totem_blocked_until_catch_end = False
        macro.totem_needs_rod_reequip = False
        macro.totem_needs_settle_delay = False
