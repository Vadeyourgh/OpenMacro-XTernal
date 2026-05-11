"""
OpenMacro XTernal - Python Edition
Fishing controller - PD-based reel balancing logic.
"""

import time
import ctypes
from dataclasses import dataclass, field
from typing import Optional

from ..core.memory import GameMemory


@dataclass
class MacroState:
    """Holds all runtime macro state."""
    phase: str = "OFF"
    power_percent: str = ""
    progress_percent: str = ""
    is_holding: bool = False
    cast_threshold: float = 96.0
    cast_wait_timeout_ms: int = 15000
    fishing_end_grace_ms: int = 100
    cast_started_at: float = 0
    cast_released_at: float = 0
    cast_bar_seen: bool = False
    fishing_lost_at: float = 0
    completion_reached: bool = False
    outcome_resolved: bool = False
    fish_caught_count: int = 0
    fish_lost_count: int = 0
    cast_timeout_count: int = 0
    totem_pop_count: int = 0
    shaking_interval_ms: int = 25
    last_shaked_at: float = 0
    last_action_at: float = 0
    cycle_enabled: bool = False

    # Totem state
    totem_state: str = "IDLE"
    totem_retry_count: int = 0
    totem_wait_started_at: float = 0
    last_totem_success_at: float = 0
    last_totem_attempt_at: float = 0
    totem_pending: bool = False
    totem_blocked_until_catch_end: bool = False
    totem_night_covered: bool = False
    totem_needs_rod_reequip: bool = False
    totem_needs_settle_delay: bool = False

    # Cached addresses
    reel_gui_addr: int = 0
    reel_bar_addr: int = 0
    fish_addr: int = 0
    playerbar_addr: int = 0
    progress_bar_addr: int = 0
    power_bar_addr: int = 0

    # Appraise state
    appraise_subvalues_addr: int = 0
    appraise_last_click_at: float = 0
    appraise_wait_started_at: float = 0
    appraise_start_coins: str = ""
    appraise_end_coins: str = ""
    appraise_state: str = "IDLE"
    appraise_last_error: str = ""

    @property
    def success_rate(self) -> float:
        total = self.fish_caught_count + self.fish_lost_count
        if total == 0:
            return 0.0
        return (self.fish_caught_count / total) * 100.0

    @property
    def display_status(self) -> str:
        if self.phase == "APPRAISE":
            return f"APPRAISE {self.appraise_state}"
        if self.totem_state != "IDLE":
            return self.totem_state
        return self.phase


class FishingController:
    """PD-based fishing reel controller."""

    def __init__(self, game: GameMemory, settings: dict):
        self.game = game
        self.settings = settings
        self.last_playerbar_pos: Optional[float] = None
        self.last_fish_pos: Optional[float] = None
        self.pwm_accumulator: float = 0.0

    def reset(self):
        self.last_playerbar_pos = None
        self.last_fish_pos = None
        self.pwm_accumulator = 0.0

    def update(self, macro: MacroState):
        """Main control loop tick for fishing phase."""
        ctx = self._get_reel_context(macro)
        if not ctx:
            self._release(macro)
            return

        fish_pos = self._get_fish_position(ctx)
        playerbar_pos = self._get_playerbar_position(ctx)

        if fish_pos is None or playerbar_pos is None:
            return

        if self.last_playerbar_pos is None:
            self.last_playerbar_pos = playerbar_pos
        if self.last_fish_pos is None:
            self.last_fish_pos = fish_pos

        playerbar_velocity = playerbar_pos - self.last_playerbar_pos
        self.last_playerbar_pos = playerbar_pos

        fish_velocity = fish_pos - self.last_fish_pos
        self.last_fish_pos = fish_pos

        error = fish_pos - playerbar_pos
        main = self.settings

        # Edge boundary check
        edge_boundary = main.get("edge_boundary", 0.1)
        if playerbar_pos < edge_boundary:
            self._hold(macro)
            return
        if playerbar_pos > 1 - edge_boundary:
            self._release(macro)
            return

        # Prediction
        prediction_scale = main.get("prediction_strength", 7.5) * (
            1.0 - main.get("resilience", 0.0)
        )
        predicted = playerbar_pos + (playerbar_velocity * prediction_scale)
        predicted_error = fish_pos - predicted

        hard_fix_threshold = 0.01
        same_side = (error * predicted_error) > 0
        approaching = (error * playerbar_velocity) > 0
        remaining_dist = max(0.0, abs(error) - hard_fix_threshold)

        brake_lookahead = abs(playerbar_velocity) * 8
        needs_pre_slow = approaching and (brake_lookahead >= remaining_dist)

        # Hard fix
        if abs(error) > hard_fix_threshold and same_side and not needs_pre_slow:
            if error > 0:
                self._hold(macro)
            else:
                self._release(macro)
            return

        neutral_duty = main.get("neutral_duty_cycle", 0.5)

        if needs_pre_slow and brake_lookahead > 0:
            brake_urgency = 1.0 - min(1.0, remaining_dist / brake_lookahead)
            if error > 0:
                target_duty = neutral_duty * (1.0 - brake_urgency)
            else:
                target_duty = neutral_duty + ((1.0 - neutral_duty) * brake_urgency)
        else:
            # PWM fine-tracking
            kP = main.get("proportional_gain", 0.42)
            kD = main.get("derivative_gain", 0.55)
            kV = main.get("velocity_damping", 38)

            adjustment = (kP * error) + (kD * fish_velocity) - (kV * playerbar_velocity)
            target_duty = max(0.0, min(1.0, neutral_duty + adjustment))

        self.pwm_accumulator += target_duty
        if self.pwm_accumulator >= 1.0:
            self.pwm_accumulator -= 1.0
            self._hold(macro)
        else:
            self._release(macro)

    def _get_reel_context(self, macro: MacroState) -> Optional[dict]:
        """Get the reel bar context (bar, fish, playerbar addresses)."""
        reel_gui = self.game.get_reel_gui()
        if not reel_gui:
            macro.reel_bar_addr = 0
            macro.fish_addr = 0
            macro.playerbar_addr = 0
            return None

        if macro.reel_bar_addr and macro.fish_addr and macro.playerbar_addr:
            return {
                "bar": macro.reel_bar_addr,
                "fish": macro.fish_addr,
                "playerbar": macro.playerbar_addr,
            }

        bar = self.game.reader.find_child_by_name(reel_gui, "bar")
        if not bar:
            return None

        fish = self.game.reader.find_child_by_name(bar, "fish")
        playerbar = self.game.reader.find_child_by_name(bar, "playerbar")

        macro.reel_bar_addr = bar
        macro.fish_addr = fish
        macro.playerbar_addr = playerbar

        if fish and playerbar:
            return {"bar": bar, "fish": fish, "playerbar": playerbar}
        return None

    def _get_fish_position(self, ctx: dict) -> Optional[float]:
        if not ctx.get("fish"):
            return None
        pos = self.game.reader.read_frame_position_x(ctx["fish"])
        size = self.game.reader.read_frame_size_x(ctx["fish"])
        return pos["scale"] + (size["scale"] / 2)

    def _get_playerbar_position(self, ctx: dict) -> Optional[float]:
        if not ctx.get("playerbar"):
            return None
        pos = self.game.reader.read_frame_position_x(ctx["playerbar"])
        return pos["scale"]

    def _hold(self, macro: MacroState):
        """Hold mouse (left button down)."""
        if not macro.is_holding:
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
            macro.is_holding = True
            macro.last_action_at = time.time()

    def _release(self, macro: MacroState):
        """Release mouse (left button up)."""
        if macro.is_holding:
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
            macro.is_holding = False
            macro.last_action_at = time.time()


def hold_mouse(macro: MacroState):
    """Global hold mouse function."""
    if not macro.is_holding:
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        macro.is_holding = True
        macro.last_action_at = time.time()


def release_mouse(macro: MacroState):
    """Global release mouse function."""
    if macro.is_holding:
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        macro.is_holding = False
        macro.last_action_at = time.time()
