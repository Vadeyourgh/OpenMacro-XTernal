"""
OpenMacro XTernal - Python Edition
Appraisal tab: Auto-appraise settings and guide.
"""

import customtkinter as ctk

from ...core.constants import MUTATIONS


class AppraisalTab(ctk.CTkFrame):
    """Appraisal tab with mutation picker and click point."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # === Settings Section ===
        settings_frame = ctk.CTkFrame(self, corner_radius=10)
        settings_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            settings_frame, text="Appraisal Settings", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Master switch
        switch_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        switch_row.pack(fill="x", padx=15, pady=5)

        self.master_switch = ctk.CTkSwitch(
            switch_row,
            text="Master Switch (Appraise mode when ON)",
            command=self._toggle_master,
        )
        self.master_switch.pack(anchor="w")
        if self.app.main_settings.get("auto_appraise_enabled"):
            self.master_switch.select()

        # Mutation picker
        mut_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        mut_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(mut_row, text="Mutation:", font=ctk.CTkFont(size=12)).pack(side="left")

        current_mutation = self.app.main_settings.get("auto_appraise_mutation", "Mythical")
        mutations = list(MUTATIONS)
        if current_mutation not in mutations:
            mutations.append(current_mutation)

        self.mutation_var = ctk.StringVar(value=current_mutation)
        self.mutation_dropdown = ctk.CTkOptionMenu(
            mut_row, variable=self.mutation_var, values=mutations, width=150,
            command=self._on_mutation_change
        )
        self.mutation_dropdown.pack(side="left", padx=10)

        # Click point
        click_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        click_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(click_row, text="Click Point:", font=ctk.CTkFont(size=12)).pack(side="left")

        self.click_x_entry = ctk.CTkEntry(click_row, width=70, justify="center", placeholder_text="X")
        x_val = self.app.main_settings.get("auto_appraise_click_x", "")
        if x_val:
            self.click_x_entry.insert(0, str(x_val))
        self.click_x_entry.pack(side="left", padx=5)

        self.click_y_entry = ctk.CTkEntry(click_row, width=70, justify="center", placeholder_text="Y")
        y_val = self.app.main_settings.get("auto_appraise_click_y", "")
        if y_val:
            self.click_y_entry.insert(0, str(y_val))
        self.click_y_entry.pack(side="left", padx=5)

        # Buttons
        btn_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkButton(btn_row, text="Pick Click Point", width=140, command=self._pick_point).pack(
            side="left", padx=(0, 10)
        )
        ctk.CTkButton(btn_row, text="Clear Point", width=120, command=self._clear_point).pack(
            side="left"
        )

        # Status
        self.status_label = ctk.CTkLabel(
            settings_frame, text="Status: Ready.", font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.status_label.pack(anchor="w", padx=15, pady=(0, 10))

        # === Guide Section ===
        guide_frame = ctk.CTkFrame(self, corner_radius=10)
        guide_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            guide_frame, text="Guide", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        guide_text = (
            "1. Hold the fish you want appraised before starting.\n"
            "2. Set the click point on the appraiser dialogue option.\n"
            "3. Press Start Macro hotkey to begin appraising.\n"
            "4. Webhook enabled: you'll be notified when done.\n\n"
            f"Start: {self.app.hotkeys.get('start_macro', 'F1')}  |  "
            f"Stop: {self.app.hotkeys.get('stop_appraise', 'F2')}"
        )

        ctk.CTkLabel(
            guide_frame, text=guide_text, font=ctk.CTkFont(size=11),
            justify="left", wraplength=350, text_color="gray"
        ).pack(anchor="w", padx=15, pady=(0, 15))

    def _toggle_master(self):
        val = 1 if self.master_switch.get() else 0
        self.app.main_settings["auto_appraise_enabled"] = val
        self.app.save_settings()

    def _on_mutation_change(self, value):
        self.app.main_settings["auto_appraise_mutation"] = value
        self.app.save_settings()

    def _pick_point(self):
        self.status_label.configure(text="Status: Right-click to set the point...")
        # In a real implementation, this would capture a mouse position
        # For now we show a dialog
        dialog = ctk.CTkInputDialog(text="Enter X,Y (e.g. 500,300):", title="Click Point")
        result = dialog.get_input()
        if result and "," in result:
            try:
                x, y = result.split(",")
                x, y = int(x.strip()), int(y.strip())
                self.click_x_entry.delete(0, "end")
                self.click_x_entry.insert(0, str(x))
                self.click_y_entry.delete(0, "end")
                self.click_y_entry.insert(0, str(y))
                self.app.main_settings["auto_appraise_click_x"] = x
                self.app.main_settings["auto_appraise_click_y"] = y
                self.app.save_settings()
                self.status_label.configure(text=f"Status: Click point saved: {x}, {y}")
            except ValueError:
                self.status_label.configure(text="Status: Invalid input.")
        else:
            self.status_label.configure(text="Status: Cancelled.")

    def _clear_point(self):
        self.click_x_entry.delete(0, "end")
        self.click_y_entry.delete(0, "end")
        self.app.main_settings["auto_appraise_click_x"] = ""
        self.app.main_settings["auto_appraise_click_y"] = ""
        self.app.save_settings()
        self.status_label.configure(text="Status: Click point cleared.")

    def set_status(self, message: str):
        self.status_label.configure(text=f"Status: {message}")
