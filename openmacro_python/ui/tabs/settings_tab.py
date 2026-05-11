"""
OpenMacro XTernal - Python Edition
Settings tab: Hotkeys, appearance/themes, update settings.
"""

import customtkinter as ctk
from tkinter import messagebox

from ...core.constants import BUILT_IN_THEMES


class SettingsTab(ctk.CTkFrame):
    """Settings tab with hotkeys, appearance, and update configuration."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # === Update Settings ===
        update_frame = ctk.CTkFrame(scroll, corner_radius=10)
        update_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            update_frame, text="Update Settings", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.auto_update_switch = ctk.CTkSwitch(
            update_frame, text="Automatic updates (install silently)",
            command=self._toggle_auto_update,
        )
        self.auto_update_switch.pack(anchor="w", padx=15, pady=3)
        if self.app.settings.get("update", {}).get("auto_update"):
            self.auto_update_switch.select()

        self.show_confirm_switch = ctk.CTkSwitch(
            update_frame, text="Show update confirmation",
            command=self._toggle_show_confirm,
        )
        self.show_confirm_switch.pack(anchor="w", padx=15, pady=(3, 10))
        if self.app.settings.get("update", {}).get("show_confirmation"):
            self.show_confirm_switch.select()

        # === Hotkeys ===
        hotkey_frame = ctk.CTkFrame(scroll, corner_radius=10)
        hotkey_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            hotkey_frame, text="Hotkeys", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.hotkey_entries = {}
        hotkey_config = [
            ("start_macro", "Start Macro", "Starts/stops the fishing macro"),
            ("stop_appraise", "Stop Appraising", "Stops an active appraise cycle"),
            ("fix_roblox", "Fix Roblox", "Re-attaches to Roblox process"),
            ("reload", "Reload", "Reloads the application"),
        ]

        for key, label, desc in hotkey_config:
            row = ctk.CTkFrame(hotkey_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)

            entry = ctk.CTkEntry(row, width=50, justify="center")
            entry.insert(0, self.app.hotkeys.get(key, ""))
            entry.pack(side="left")
            entry.bind("<FocusOut>", lambda e, k=key: self._on_hotkey_change(k))

            label_frame = ctk.CTkFrame(row, fg_color="transparent")
            label_frame.pack(side="left", padx=10)
            ctk.CTkLabel(label_frame, text=label, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(label_frame, text=desc, font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w")

            self.hotkey_entries[key] = entry

        # padding at bottom of hotkey section
        ctk.CTkLabel(hotkey_frame, text="").pack(pady=5)

        # === Appearance ===
        appearance_frame = ctk.CTkFrame(scroll, corner_radius=10)
        appearance_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            appearance_frame, text="Appearance", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Theme selector
        theme_row = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        theme_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(theme_row, text="Theme:", font=ctk.CTkFont(size=12)).pack(side="left")

        theme_names = list(BUILT_IN_THEMES.keys()) + ["Custom"]
        last_theme = self.app.settings.get("last_theme", "Default")
        self.theme_var = ctk.StringVar(value=last_theme)
        self.theme_dropdown = ctk.CTkOptionMenu(
            theme_row, variable=self.theme_var, values=theme_names, width=130,
            command=self._on_theme_change,
        )
        self.theme_dropdown.pack(side="left", padx=10)

        # Color entries
        self.color_entries = {}
        color_config = [
            ("accent_color", "Accent Color"),
            ("bg_color", "Background"),
            ("text_color", "Text Color"),
            ("border_color", "Border Color"),
        ]

        for key, label in color_config:
            row = ctk.CTkFrame(appearance_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)

            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), width=120).pack(side="left")

            entry = ctk.CTkEntry(row, width=100, justify="center")
            val = self.app.settings.get("appearance", {}).get(key, "")
            entry.insert(0, val)
            entry.pack(side="left", padx=5)

            # Color swatch
            try:
                swatch = ctk.CTkLabel(row, text="  ", width=25, fg_color=f"#{val}")
                swatch.pack(side="left", padx=5)
            except Exception:
                pass

            self.color_entries[key] = entry

        # Apply button
        ctk.CTkButton(
            appearance_frame, text="Apply Theme", width=120, command=self._apply_appearance
        ).pack(anchor="w", padx=15, pady=(5, 15))

    def _toggle_auto_update(self):
        val = 1 if self.auto_update_switch.get() else 0
        self.app.settings.setdefault("update", {})["auto_update"] = val
        self.app.save_settings()

    def _toggle_show_confirm(self):
        val = 1 if self.show_confirm_switch.get() else 0
        self.app.settings.setdefault("update", {})["show_confirmation"] = val
        self.app.save_settings()

    def _on_hotkey_change(self, key: str):
        entry = self.hotkey_entries.get(key)
        if not entry:
            return
        new_key = entry.get().strip()
        old_key = self.app.hotkeys.get(key, "")
        if new_key == old_key:
            return

        # Check conflicts
        for action, assigned in self.app.hotkeys.items():
            if action != key and assigned == new_key:
                entry.delete(0, "end")
                entry.insert(0, old_key)
                messagebox.showwarning(
                    "Conflict", f"{new_key} is already assigned to {action}."
                )
                return

        self.app.change_hotkey(key, old_key, new_key)

    def _on_theme_change(self, theme_name: str):
        if theme_name == "Custom":
            custom = self.app.settings.get("custom_theme", {})
            for key, entry in self.color_entries.items():
                entry.delete(0, "end")
                entry.insert(0, custom.get(key, ""))
        elif theme_name in BUILT_IN_THEMES:
            theme = BUILT_IN_THEMES[theme_name]
            for key, entry in self.color_entries.items():
                entry.delete(0, "end")
                entry.insert(0, theme.get(key, ""))

    def _apply_appearance(self):
        new_colors = {}
        for key, entry in self.color_entries.items():
            raw = entry.get().strip().upper()
            if not all(c in "0123456789ABCDEF" for c in raw) or len(raw) != 6:
                messagebox.showwarning("Invalid Color", f"Invalid hex color for {key}: {raw}")
                return
            new_colors[key] = raw.lower()

        self.app.settings["appearance"] = new_colors
        self.app.settings["last_theme"] = self.theme_var.get()
        if self.theme_var.get() == "Custom":
            self.app.settings["custom_theme"] = dict(new_colors)
        self.app.save_settings()
        messagebox.showinfo("Applied", "Theme applied. Restart for full effect.")
