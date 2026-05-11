"""
OpenMacro XTernal - Python Edition
Home tab: Adjustments, main stats, config management.
"""

import customtkinter as ctk
from tkinter import messagebox


class HomeTab(ctk.CTkFrame):
    """Home tab with adjustments, live stats, and config management."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # === Adjustments Section ===
        adj_frame = ctk.CTkFrame(self, corner_radius=10)
        adj_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            adj_frame, text="Adjustments", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Settings grid
        grid_frame = ctk.CTkFrame(adj_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.entries = {}
        settings_config = [
            ("update_rate", "Update Rate", "1 - 35", True),
            ("prediction_strength", "Prediction Strength", "1.0 - 20.0", False),
            ("neutral_duty_cycle", "Neutral Duty Cycle", "0.20 - 0.60", False),
            ("velocity_damping", "Velocity Damping", "10 - 60", True),
            ("proportional_gain", "Proportional Gain", "0.10 - 1.50", False),
            ("derivative_gain", "Derivative Gain", "0.00 - 1.00", False),
            ("edge_boundary", "Edge Boundary", "0.02 - 0.30", False),
        ]

        for row, (key, label, range_text, is_int) in enumerate(settings_config):
            ctk.CTkLabel(grid_frame, text=label, font=ctk.CTkFont(size=12)).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=3
            )

            value = self.app.main_settings.get(key, 0)
            display = str(int(value)) if is_int else f"{value:.2f}"

            entry = ctk.CTkEntry(grid_frame, width=70, justify="center")
            entry.insert(0, display)
            entry.grid(row=row, column=1, padx=5, pady=3)
            entry.bind("<FocusOut>", lambda e, k=key: self._on_setting_change(k))

            ctk.CTkLabel(
                grid_frame, text=range_text, font=ctk.CTkFont(size=11), text_color="gray"
            ).grid(row=row, column=2, sticky="w", padx=5, pady=3)

            self.entries[key] = entry

        grid_frame.columnconfigure(0, weight=1)

        # === Main Section (Rod + Resilience) ===
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            main_frame, text="Main", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        info_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_grid.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(info_grid, text="Rod Resilience:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="w", pady=3
        )
        resilience = self.app.main_settings.get("resilience", 0.0)
        self.resilience_entry = ctk.CTkEntry(info_grid, width=70, justify="center")
        self.resilience_entry.insert(0, f"{resilience:.2f}")
        self.resilience_entry.grid(row=0, column=1, padx=10, pady=3)
        self.resilience_entry.bind("<FocusOut>", lambda e: self._on_setting_change("resilience"))
        self.entries["resilience"] = self.resilience_entry

        ctk.CTkLabel(info_grid, text="Rod Equipped:", font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky="w", pady=3
        )
        self.rod_label = ctk.CTkLabel(
            info_grid, text=self.app.game.rod_name or "---", font=ctk.CTkFont(size=12)
        )
        self.rod_label.grid(row=1, column=1, sticky="w", padx=10, pady=3)

        info_grid.columnconfigure(0, weight=1)

        # === Live Status ===
        status_frame = ctk.CTkFrame(self, corner_radius=10)
        status_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            status_frame, text="Status", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        stats_grid = ctk.CTkFrame(status_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=15, pady=(0, 10))

        self.status_label = ctk.CTkLabel(stats_grid, text="Status: OFF", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=0, column=0, sticky="w", pady=2)

        self.power_label = ctk.CTkLabel(stats_grid, text="Power: ---", font=ctk.CTkFont(size=12))
        self.power_label.grid(row=1, column=0, sticky="w", pady=2)

        self.progress_label = ctk.CTkLabel(stats_grid, text="Progress: ---", font=ctk.CTkFont(size=12))
        self.progress_label.grid(row=2, column=0, sticky="w", pady=2)

        self.caught_label = ctk.CTkLabel(stats_grid, text="Caught: 0", font=ctk.CTkFont(size=12))
        self.caught_label.grid(row=0, column=1, sticky="w", padx=(50, 0), pady=2)

        self.lost_label = ctk.CTkLabel(stats_grid, text="Lost: 0", font=ctk.CTkFont(size=12))
        self.lost_label.grid(row=1, column=1, sticky="w", padx=(50, 0), pady=2)

        self.rate_label = ctk.CTkLabel(stats_grid, text="Success Rate: 0.0%", font=ctk.CTkFont(size=12))
        self.rate_label.grid(row=2, column=1, sticky="w", padx=(50, 0), pady=2)

        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)

        # === Config Section ===
        config_frame = ctk.CTkFrame(self, corner_radius=10)
        config_frame.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(
            config_frame, text="Config Profiles", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        config_row = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_row.pack(fill="x", padx=15, pady=(0, 10))

        configs = self.app.list_configs()
        self.config_var = ctk.StringVar(value=configs[0] if configs else "No configs")
        self.config_dropdown = ctk.CTkOptionMenu(
            config_row, variable=self.config_var, values=configs or ["No configs"], width=150
        )
        self.config_dropdown.pack(side="left", padx=(0, 10))

        ctk.CTkButton(config_row, text="Load", width=60, command=self._load_config).pack(side="left", padx=2)
        ctk.CTkButton(config_row, text="Save", width=60, command=self._save_config).pack(side="left", padx=2)
        ctk.CTkButton(config_row, text="New", width=60, command=self._new_config).pack(side="left", padx=2)
        ctk.CTkButton(config_row, text="Del", width=60, command=self._delete_config).pack(side="left", padx=2)

    def update_status(self, macro):
        """Update live status display from macro state."""
        self.status_label.configure(text=f"Status: {macro.display_status}")
        power = macro.power_percent if macro.power_percent else "---"
        self.power_label.configure(text=f"Power: {power}")
        progress = macro.progress_percent if macro.progress_percent else "---"
        self.progress_label.configure(text=f"Progress: {progress}")
        self.caught_label.configure(text=f"Caught: {macro.fish_caught_count}")
        self.lost_label.configure(text=f"Lost: {macro.fish_lost_count}")
        self.rate_label.configure(text=f"Success Rate: {macro.success_rate:.1f}%")
        self.rod_label.configure(text=self.app.game.rod_name or "---")

    def _on_setting_change(self, key: str):
        """Validate and save a setting when its entry loses focus."""
        entry = self.entries.get(key)
        if not entry:
            return

        raw = entry.get().strip()
        try:
            value = float(raw)
        except ValueError:
            # Reset to current
            current = self.app.main_settings.get(key, 0)
            entry.delete(0, "end")
            entry.insert(0, str(current))
            return

        self.app.main_settings[key] = value
        self.app.save_settings()

    def _load_config(self):
        name = self.config_var.get()
        if name == "No configs":
            return
        self.app.load_config(name)
        self._refresh_entries()

    def _save_config(self):
        name = self.config_var.get()
        if name == "No configs":
            return
        self.app.save_config(name)

    def _new_config(self):
        dialog = ctk.CTkInputDialog(text="Config name:", title="New Config")
        name = dialog.get_input()
        if name and name.strip():
            name = name.strip()
            self.app.save_config(name)
            self._refresh_config_list()

    def _delete_config(self):
        name = self.config_var.get()
        if name == "No configs":
            return
        self.app.delete_config(name)
        self._refresh_config_list()

    def _refresh_config_list(self):
        configs = self.app.list_configs()
        values = configs if configs else ["No configs"]
        self.config_dropdown.configure(values=values)
        self.config_var.set(values[0])

    def _refresh_entries(self):
        for key, entry in self.entries.items():
            val = self.app.main_settings.get(key, 0)
            entry.delete(0, "end")
            if isinstance(val, int):
                entry.insert(0, str(val))
            else:
                entry.insert(0, f"{val:.2f}")
