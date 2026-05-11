"""
OpenMacro XTernal - Python Edition
Advanced Settings tab: Cast power, timing, fishing behavior, auto-totem.
"""

import customtkinter as ctk


class AdvancedTab(ctk.CTkFrame):
    """Advanced settings tab with casting, timing, and behavior controls."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # === Cast Settings ===
        cast_frame = ctk.CTkFrame(scroll, corner_radius=10)
        cast_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            cast_frame, text="Cast Settings", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Cast Mode
        mode_row = ctk.CTkFrame(cast_frame, fg_color="transparent")
        mode_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(mode_row, text="Cast Mode:", font=ctk.CTkFont(size=12)).pack(side="left")

        current_mode = self.app.main_settings.get("cast_mode", "short")
        self.cast_mode_var = ctk.StringVar(value=current_mode)
        modes = ["short", "full", "custom"]
        self.cast_mode_menu = ctk.CTkOptionMenu(
            mode_row, variable=self.cast_mode_var, values=modes, width=120,
            command=self._on_cast_mode_change
        )
        self.cast_mode_menu.pack(side="left", padx=10)

        ctk.CTkLabel(
            mode_row, text="short=28% | full=96% | custom", font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(side="left", padx=5)

        # Custom Cast Power
        power_row = ctk.CTkFrame(cast_frame, fg_color="transparent")
        power_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(power_row, text="Custom Cast Power (%):", font=ctk.CTkFont(size=12)).pack(side="left")
        self.cast_power_entry = ctk.CTkEntry(power_row, width=70, justify="center")
        self.cast_power_entry.insert(0, str(self.app.main_settings.get("cast_power_custom", 96.0)))
        self.cast_power_entry.pack(side="left", padx=10)
        self.cast_power_entry.bind("<FocusOut>", lambda e: self._save_numeric("cast_power_custom", self.cast_power_entry, 1.0, 100.0))

        ctk.CTkLabel(power_row, text="1.0 - 100.0", font=ctk.CTkFont(size=10), text_color="gray").pack(side="left")

        ctk.CTkLabel(cast_frame, text="").pack(pady=3)

        # === Timing Settings ===
        timing_frame = ctk.CTkFrame(scroll, corner_radius=10)
        timing_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            timing_frame, text="Timing", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.timing_entries = {}
        timing_config = [
            ("pre_cast_delay_ms", "Pre-Cast Delay (ms)", "0 - 5000", "Delay before re-casting after catching a fish"),
            ("post_cast_delay_ms", "Post-Cast Delay (ms)", "0 - 2000", "Delay after releasing cast before shake phase"),
            ("cast_timeout_ms", "Cast Timeout (ms)", "5000 - 60000", "Max time to wait for power bar"),
            ("shake_interval_ms", "Shake Interval (ms)", "10 - 500", "How often to press Enter while waiting for bite"),
            ("fishing_action_delay_ms", "Fishing Action Delay (ms)", "0 - 200", "Min time between hold/release actions"),
        ]

        for key, label, range_text, tooltip in timing_config:
            row = ctk.CTkFrame(timing_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)

            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), width=200).pack(side="left")

            entry = ctk.CTkEntry(row, width=70, justify="center")
            entry.insert(0, str(int(self.app.main_settings.get(key, 0))))
            entry.pack(side="left", padx=10)
            entry.bind("<FocusOut>", lambda e, k=key, ent=entry: self._save_int(k, ent))

            ctk.CTkLabel(row, text=range_text, font=ctk.CTkFont(size=10), text_color="gray").pack(side="left")
            self.timing_entries[key] = entry

        ctk.CTkLabel(timing_frame, text="").pack(pady=3)

        # === Fishing Behavior ===
        behavior_frame = ctk.CTkFrame(scroll, corner_radius=10)
        behavior_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            behavior_frame, text="Fishing Behavior", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Completion threshold
        comp_row = ctk.CTkFrame(behavior_frame, fg_color="transparent")
        comp_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(comp_row, text="Completion Threshold (%):", font=ctk.CTkFont(size=12)).pack(side="left")
        self.completion_entry = ctk.CTkEntry(comp_row, width=70, justify="center")
        self.completion_entry.insert(0, str(self.app.main_settings.get("completion_threshold", 99.7)))
        self.completion_entry.pack(side="left", padx=10)
        self.completion_entry.bind("<FocusOut>", lambda e: self._save_numeric("completion_threshold", self.completion_entry, 50.0, 100.0))
        ctk.CTkLabel(comp_row, text="50.0 - 100.0", font=ctk.CTkFont(size=10), text_color="gray").pack(side="left")

        # Cast on timeout switch
        self.cast_on_timeout_switch = ctk.CTkSwitch(
            behavior_frame, text="Re-cast on timeout (otherwise stop macro)",
            command=self._toggle_cast_on_timeout,
        )
        self.cast_on_timeout_switch.pack(anchor="w", padx=15, pady=5)
        if self.app.main_settings.get("cast_on_timeout", 1):
            self.cast_on_timeout_switch.select()

        ctk.CTkLabel(behavior_frame, text="").pack(pady=3)

        # === Auto Totem ===
        totem_frame = ctk.CTkFrame(scroll, corner_radius=10)
        totem_frame.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(
            totem_frame, text="Auto Totem", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Enable switch
        self.totem_switch = ctk.CTkSwitch(
            totem_frame, text="Enable Auto Totem (Aurora Totem)",
            command=self._toggle_totem,
        )
        self.totem_switch.pack(anchor="w", padx=15, pady=5)
        if self.app.main_settings.get("auto_totem_enabled", 0):
            self.totem_switch.select()

        # Mode
        totem_mode_row = ctk.CTkFrame(totem_frame, fg_color="transparent")
        totem_mode_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(totem_mode_row, text="Totem Mode:", font=ctk.CTkFont(size=12)).pack(side="left")
        current_totem_mode = self.app.main_settings.get("auto_totem_mode", "expire")
        self.totem_mode_var = ctk.StringVar(value=current_totem_mode)
        self.totem_mode_menu = ctk.CTkOptionMenu(
            totem_mode_row, variable=self.totem_mode_var, values=["expire", "interval"], width=120,
            command=self._on_totem_mode_change
        )
        self.totem_mode_menu.pack(side="left", padx=10)

        # Interval
        interval_row = ctk.CTkFrame(totem_frame, fg_color="transparent")
        interval_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(interval_row, text="Interval (seconds):", font=ctk.CTkFont(size=12)).pack(side="left")
        self.totem_interval_entry = ctk.CTkEntry(interval_row, width=70, justify="center")
        self.totem_interval_entry.insert(0, str(int(self.app.main_settings.get("auto_totem_interval_sec", 900))))
        self.totem_interval_entry.pack(side="left", padx=10)
        self.totem_interval_entry.bind("<FocusOut>", lambda e: self._save_int("auto_totem_interval_sec", self.totem_interval_entry))

        ctk.CTkLabel(interval_row, text="(only for interval mode)", font=ctk.CTkFont(size=10), text_color="gray").pack(side="left")

        ctk.CTkLabel(totem_frame, text="").pack(pady=5)

    # === Callbacks ===

    def _on_cast_mode_change(self, value):
        self.app.main_settings["cast_mode"] = value
        self.app.save_settings()

    def _on_totem_mode_change(self, value):
        self.app.main_settings["auto_totem_mode"] = value
        self.app.save_settings()

    def _toggle_cast_on_timeout(self):
        val = 1 if self.cast_on_timeout_switch.get() else 0
        self.app.main_settings["cast_on_timeout"] = val
        self.app.save_settings()

    def _toggle_totem(self):
        val = 1 if self.totem_switch.get() else 0
        self.app.main_settings["auto_totem_enabled"] = val
        self.app.save_settings()

    def _save_numeric(self, key: str, entry, min_val: float, max_val: float):
        try:
            value = float(entry.get().strip())
            value = max(min_val, min(max_val, value))
            self.app.main_settings[key] = value
            entry.delete(0, "end")
            entry.insert(0, f"{value:.1f}" if value != int(value) else str(int(value)))
            self.app.save_settings()
        except ValueError:
            # Reset to current
            entry.delete(0, "end")
            entry.insert(0, str(self.app.main_settings.get(key, 0)))

    def _save_int(self, key: str, entry):
        try:
            value = int(float(entry.get().strip()))
            value = max(0, value)
            self.app.main_settings[key] = value
            entry.delete(0, "end")
            entry.insert(0, str(value))
            self.app.save_settings()
        except ValueError:
            entry.delete(0, "end")
            entry.insert(0, str(int(self.app.main_settings.get(key, 0))))
