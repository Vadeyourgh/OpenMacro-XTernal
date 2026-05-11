"""
OpenMacro XTernal - Python Edition
Main application GUI built with CustomTkinter.
"""

import sys
import time
import threading
import customtkinter as ctk

from ..core.constants import FULL_VER, get_default_settings
from ..core.settings import (
    ensure_app_data_dirs, load_settings, save_settings,
    list_configs, save_config, load_config, delete_config,
)
from ..core.memory import GameMemory
from ..features.fish import MacroState, FishingController, hold_mouse, release_mouse
from ..features.totem import TotemManager
from ..features.appraise import AppraiseManager
from ..features.webhook import WebhookManager
from ..features.hotkeys import HotkeyManager

from .tabs.home_tab import HomeTab
from .tabs.appraisal_tab import AppraisalTab
from .tabs.settings_tab import SettingsTab
from .tabs.webhook_tab import WebhookTab
from .tabs.about_tab import AboutTab


class OpenMacroApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Initialize core systems
        ensure_app_data_dirs()
        self.settings = load_settings()
        self.main_settings = self.settings.get("main", get_default_settings()["main"])
        self.hotkeys = self.settings.get("hotkeys", get_default_settings()["hotkeys"])
        self.appearance = self.settings.get("appearance", get_default_settings()["appearance"])

        # Apply theme
        self._apply_theme()

        # Window setup
        self.title(f"OpenMacro XTernal | {FULL_VER}")
        self.geometry("480x720")
        self.minsize(460, 650)
        self.resizable(True, True)

        # Core objects
        self.game = GameMemory()
        self.macro = MacroState()
        self.controller = FishingController(self.game, self.main_settings)
        self.totem_mgr = TotemManager(self.game, self.main_settings)
        self.appraise_mgr = AppraiseManager(self.game, self.main_settings)
        self.webhook = WebhookManager(self.settings)
        self.hotkey_mgr = HotkeyManager()

        # Macro loop
        self._macro_running = False
        self._loop_thread = None

        # Build UI
        self._build_ui()

        # Register hotkeys
        self._register_hotkeys()

        # Try to attach to Roblox on startup
        self._try_attach_startup()

        # Start UI update loop
        self._update_ui_loop()

        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_theme(self):
        """Apply the color theme via CustomTkinter."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def _build_ui(self):
        """Build the main tabbed interface."""
        # Header bar
        header = ctk.CTkFrame(self, height=40, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"OpenMacro XTernal {FULL_VER}",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=15, pady=8)

        self.pid_label = ctk.CTkLabel(
            header,
            text="PID: ---",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.pid_label.pack(side="right", padx=15, pady=8)

        # Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Create tabs
        self.tabview.add("Home")
        self.tabview.add("Appraisal")
        self.tabview.add("Webhook")
        self.tabview.add("Settings")
        self.tabview.add("About")

        # Populate tabs
        self.home_tab = HomeTab(self.tabview.tab("Home"), self)
        self.home_tab.pack(fill="both", expand=True)

        self.appraisal_tab = AppraisalTab(self.tabview.tab("Appraisal"), self)
        self.appraisal_tab.pack(fill="both", expand=True)

        self.webhook_tab = WebhookTab(self.tabview.tab("Webhook"), self)
        self.webhook_tab.pack(fill="both", expand=True)

        self.settings_tab = SettingsTab(self.tabview.tab("Settings"), self)
        self.settings_tab.pack(fill="both", expand=True)

        self.about_tab = AboutTab(self.tabview.tab("About"), self)
        self.about_tab.pack(fill="both", expand=True)

        # Bottom bar with quick actions
        bottom = ctk.CTkFrame(self, height=45, corner_radius=0)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        self.start_btn = ctk.CTkButton(
            bottom, text="Start Macro (F1)", width=140, command=self.toggle_macro
        )
        self.start_btn.pack(side="left", padx=10, pady=8)

        self.fix_btn = ctk.CTkButton(
            bottom, text="Fix Roblox (F3)", width=130, fg_color="gray30",
            command=self.fix_roblox
        )
        self.fix_btn.pack(side="left", padx=5, pady=8)

        self.status_indicator = ctk.CTkLabel(
            bottom, text="OFF", font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ff4c4c",
        )
        self.status_indicator.pack(side="right", padx=15, pady=8)

    def _register_hotkeys(self):
        """Register global hotkeys."""
        callbacks = {
            "start_macro": self.toggle_macro,
            "stop_appraise": self._stop_appraise,
            "fix_roblox": self.fix_roblox,
            "reload": self._reload,
        }
        self.hotkey_mgr.register_all(self.hotkeys, callbacks)

    def _try_attach_startup(self):
        """Try to attach to Roblox on startup (non-blocking)."""
        def _attach():
            try:
                pid = self.game.process.get_roblox_pid()
                if pid:
                    self.game.attach(pid)
            except Exception:
                pass

        threading.Thread(target=_attach, daemon=True).start()

    def _update_ui_loop(self):
        """Periodic UI update (every 100ms)."""
        # Update PID
        pid = self.game.process.pid if self.game.process.is_attached else 0
        self.pid_label.configure(text=f"PID: {pid or '---'}")

        # Update status indicator
        if self.macro.cycle_enabled:
            self.status_indicator.configure(text="RUNNING", text_color="#3ddfa0")
            self.start_btn.configure(text="Stop Macro (F1)", fg_color="#ff4c4c")
        else:
            self.status_indicator.configure(text="OFF", text_color="#ff4c4c")
            self.start_btn.configure(text="Start Macro (F1)", fg_color=("#3B8ED0", "#1F6AA5"))

        # Update home tab
        self.home_tab.update_status(self.macro)

        # Schedule next update
        self.after(100, self._update_ui_loop)

    # === Public API ===

    def toggle_macro(self):
        """Toggle the macro on/off."""
        if self.macro.cycle_enabled:
            self._stop_macro()
        else:
            self._start_macro()

    def _start_macro(self):
        """Start the macro cycle."""
        if not self.game.is_ready:
            try:
                pid = self.game.process.get_roblox_pid()
                if not pid:
                    self._show_error("Roblox is not running.")
                    return
                self.game.attach(pid)
            except Exception as e:
                self._show_error(str(e))
                return

        # Check if appraise mode
        if self.main_settings.get("auto_appraise_enabled"):
            success, msg = self.appraise_mgr.start_cycle(self.macro)
            if not success:
                self._show_error(msg)
                return
            self.appraisal_tab.set_status(msg)
            self._start_loop()
            return

        self.macro.cycle_enabled = True
        self.macro.phase = "CASTING"
        self.macro.cast_started_at = time.time()
        self.macro.cast_threshold = self._resolve_cast_threshold()
        self.macro.cast_wait_timeout_ms = max(5000, int(self.main_settings.get("cast_timeout_ms", 15000)))
        self.macro.shaking_interval_ms = int(self.main_settings.get("shake_interval_ms", 25))

        self.webhook.start_session()
        self._start_loop()

    def _stop_macro(self):
        """Stop the macro."""
        self._macro_running = False
        self.macro.cycle_enabled = False
        release_mouse(self.macro)
        self.controller.reset()
        self.macro.phase = "OFF"

    def _stop_appraise(self):
        """Stop appraise from hotkey."""
        if self.macro.phase == "APPRAISE" and self.macro.cycle_enabled:
            self.appraise_mgr.stop_cycle(self.macro, "Stopped by hotkey.")
            self._macro_running = False
            self.appraisal_tab.set_status("Stopped by hotkey.")

    def fix_roblox(self):
        """Re-attach to Roblox."""
        self.game.reset_cache()
        try:
            pid = self.game.process.get_roblox_pid()
            if not pid:
                self.game.detach()
                self._show_error("Roblox not found.")
                return
            self.game.attach(pid)
            self._show_info("Roblox attachment refreshed.")
        except Exception as e:
            self._show_error(str(e))

    def _reload(self):
        """Reload the app (restart)."""
        self._on_close()

    def _start_loop(self):
        """Start the macro loop in a background thread."""
        if self._macro_running:
            return
        self._macro_running = True
        self._loop_thread = threading.Thread(target=self._macro_loop, daemon=True)
        self._loop_thread.start()

    def _macro_loop(self):
        """Background macro loop."""
        while self._macro_running and self.macro.cycle_enabled:
            try:
                update_rate_ms = int(self.main_settings.get("update_rate", 21))
                interval = update_rate_ms / 1000.0

                if self.macro.phase == "APPRAISE":
                    msg = self.appraise_mgr.update(self.macro)
                    if self.macro.phase in ("DONE", "FAILED"):
                        self._macro_running = False
                        break
                elif self.macro.phase == "FISHING":
                    self.controller.update(self.macro)
                    self._check_fishing_completion()
                elif self.macro.phase == "CASTING":
                    self._update_casting()
                elif self.macro.phase == "SHAKE":
                    self._update_shake()
                elif self.macro.phase == "DONE":
                    if self.macro.cycle_enabled:
                        self._restart_cast()
                    else:
                        self._macro_running = False
                        break

                # Webhook
                self.webhook.send_summary(
                    self.macro, self.game.rod_name,
                    self.settings.get("last_config", "")
                )

                time.sleep(interval)
            except Exception:
                time.sleep(0.05)

    def _update_casting(self):
        """Handle CASTING phase."""
        hold_mouse(self.macro)
        elapsed_ms = (time.time() - self.macro.cast_started_at) * 1000

        # Try to read power bar
        power_bar = self._resolve_power_bar()
        if power_bar:
            self.macro.cast_bar_seen = True
            percent = self.game.reader.read_power_bar_percent(power_bar)
            self.macro.power_percent = f"{percent:.1f}"

            if percent >= self.macro.cast_threshold:
                release_mouse(self.macro)
                self.macro.cast_released_at = time.time()
                self.macro.phase = "SHAKE"
                return
        else:
            self.macro.power_percent = ""

        if elapsed_ms >= self.macro.cast_wait_timeout_ms:
            self.macro.cast_timeout_count += 1
            if self.main_settings.get("cast_on_timeout", 1):
                self._restart_cast()
            else:
                self._stop_macro()

    def _update_shake(self):
        """Handle SHAKE phase (waiting for fish to bite)."""
        release_mouse(self.macro)
        self.macro.power_percent = ""

        # Check if fishing context is available
        ctx = self.controller._get_reel_context(self.macro)
        if ctx and ctx.get("fish") and ctx.get("playerbar"):
            self.macro.phase = "FISHING"
            self.macro.fishing_lost_at = 0
            return

        # Send Enter to shake
        now = time.time()
        shake_interval_s = self.macro.shaking_interval_ms / 1000.0
        if not self.macro.last_shaked_at or (now - self.macro.last_shaked_at) >= shake_interval_s:
            import keyboard
            keyboard.press_and_release("enter")
            self.macro.last_shaked_at = now

        # Timeout check
        if self.macro.cast_released_at:
            elapsed_ms = (now - self.macro.cast_released_at) * 1000
            if elapsed_ms >= self.macro.cast_wait_timeout_ms:
                self._restart_cast()

    def _check_fishing_completion(self):
        """Check if fishing is complete."""
        progress = self._get_fishing_progress()
        if progress is not None:
            self.macro.progress_percent = f"{progress:.0f}"
            threshold = float(self.main_settings.get("completion_threshold", 99.7))
            if progress >= threshold:
                self.macro.completion_reached = True
        else:
            self.macro.progress_percent = ""

        # Check if reel context is gone
        ctx = self.controller._get_reel_context(self.macro)
        if not ctx or not ctx.get("fish"):
            if not self.macro.fishing_lost_at:
                self.macro.fishing_lost_at = time.time()

            elapsed_ms = (time.time() - self.macro.fishing_lost_at) * 1000
            if elapsed_ms >= self.macro.fishing_end_grace_ms:
                if not self.macro.outcome_resolved:
                    self.macro.outcome_resolved = True
                    if self.macro.completion_reached:
                        self.macro.fish_caught_count += 1
                    else:
                        self.macro.fish_lost_count += 1
                self.macro.phase = "DONE"
        else:
            self.macro.fishing_lost_at = 0

    def _restart_cast(self):
        """Restart the cast cycle."""
        release_mouse(self.macro)
        self.controller.reset()
        self.macro.power_percent = ""
        self.macro.progress_percent = ""
        self.macro.cast_started_at = time.time()
        self.macro.cast_released_at = 0
        self.macro.cast_bar_seen = False
        self.macro.fishing_lost_at = 0
        self.macro.completion_reached = False
        self.macro.outcome_resolved = False
        self.macro.last_shaked_at = 0
        self.macro.cast_threshold = self._resolve_cast_threshold()
        self.macro.phase = "CASTING"

    def _resolve_cast_threshold(self) -> float:
        mode = self.main_settings.get("cast_mode", "short")
        if mode == "short":
            return 28.0
        elif mode == "custom":
            return max(1.0, min(100.0, float(self.main_settings.get("cast_power_custom", 96.0))))
        return 96.0

    def _resolve_power_bar(self) -> int:
        """Find the power bar in the game tree."""
        if self.macro.power_bar_addr:
            return self.macro.power_bar_addr
        if not self.game.is_ready:
            return 0

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
        root_part = self.game.reader.find_child_by_name(character, "HumanoidRootPart")
        if not root_part:
            return 0
        power_gui = self.game.reader.find_child_by_name(root_part, "power")
        if not power_gui:
            return 0
        bar = self.game.reader.find_descendant_by_name_and_class(power_gui, "bar", "Frame")
        if bar:
            self.macro.power_bar_addr = bar
        return bar

    def _get_fishing_progress(self) -> float:
        """Get the fishing completion percentage."""
        reel_gui = self.game.get_reel_gui()
        if not reel_gui:
            return None
        bar = self.game.reader.find_child_by_name(reel_gui, "bar")
        if not bar:
            return None
        progress_frame = self.game.reader.find_child_by_name(bar, "progress")
        if not progress_frame:
            return None
        progress_bar = self.game.reader.find_child_by_name(progress_frame, "bar")
        if not progress_bar:
            return None
        return self.game.reader.read_progress_bar_percent(progress_bar)

    # === Settings API ===

    def save_settings(self):
        self.settings["main"] = self.main_settings
        self.settings["hotkeys"] = self.hotkeys
        save_settings(self.settings)

    def list_configs(self):
        return list_configs()

    def save_config(self, name: str):
        save_config(name, self.main_settings)
        self.settings["last_config"] = name
        self.save_settings()

    def load_config(self, name: str):
        try:
            config_data = load_config(name)
            self.main_settings.update(config_data)
            self.settings["main"] = self.main_settings
            self.settings["last_config"] = name
            self.save_settings()
        except Exception:
            pass

    def delete_config(self, name: str):
        delete_config(name)
        if self.settings.get("last_config") == name:
            self.settings["last_config"] = ""
            self.save_settings()

    def change_hotkey(self, action: str, old_key: str, new_key: str):
        callbacks = {
            "start_macro": self.toggle_macro,
            "stop_appraise": self._stop_appraise,
            "fix_roblox": self.fix_roblox,
            "reload": self._reload,
        }
        self.hotkey_mgr.change_hotkey(old_key, new_key, callbacks.get(action, lambda: None))
        self.hotkeys[action] = new_key
        self.save_settings()

    def _show_error(self, msg: str):
        """Show error in a thread-safe way."""
        from tkinter import messagebox
        try:
            messagebox.showerror("Error", msg)
        except Exception:
            pass

    def _show_info(self, msg: str):
        """Show info in a thread-safe way."""
        from tkinter import messagebox
        try:
            messagebox.showinfo("Info", msg)
        except Exception:
            pass

    def _on_close(self):
        """Clean up on close."""
        self._macro_running = False
        self.macro.cycle_enabled = False
        release_mouse(self.macro)
        self.hotkey_mgr.unregister_all()
        self.game.detach()
        self.destroy()
        sys.exit(0)
