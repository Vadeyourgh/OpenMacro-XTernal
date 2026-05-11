"""
OpenMacro XTernal - Python Edition
Webhook tab: Discord webhook configuration.
"""

import customtkinter as ctk
from tkinter import messagebox


class WebhookTab(ctk.CTkFrame):
    """Webhook configuration tab."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # === Webhook Settings ===
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            main_frame, text="Discord Webhook", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Enable switch
        self.enabled_switch = ctk.CTkSwitch(
            main_frame, text="Enable Webhook Notifications",
            command=self._toggle_enabled,
        )
        self.enabled_switch.pack(anchor="w", padx=15, pady=5)
        if self.app.main_settings.get("webhook_enabled"):
            self.enabled_switch.select()

        # URL
        url_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        url_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(url_row, text="Webhook URL:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.url_entry = ctk.CTkEntry(url_row, width=350, placeholder_text="https://discord.com/api/webhooks/...")
        url = self.app.main_settings.get("webhook_url", "")
        if url:
            self.url_entry.insert(0, url)
        self.url_entry.pack(anchor="w", pady=3)
        self.url_entry.bind("<FocusOut>", self._save_url)

        # Interval
        interval_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        interval_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(interval_row, text="Summary Interval (minutes):", font=ctk.CTkFont(size=12)).pack(side="left")
        self.interval_entry = ctk.CTkEntry(interval_row, width=60, justify="center")
        self.interval_entry.insert(0, str(self.app.main_settings.get("webhook_summary_interval_min", 30)))
        self.interval_entry.pack(side="left", padx=10)
        self.interval_entry.bind("<FocusOut>", self._save_interval)

        ctk.CTkLabel(main_frame, text="").pack(pady=3)

        # === Summary Fields ===
        fields_frame = ctk.CTkFrame(self, corner_radius=10)
        fields_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            fields_frame, text="Summary Fields", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.field_switches = {}
        fields = [
            ("webhook_summary_fish", "Fish Caught/Lost"),
            ("webhook_summary_success_rate", "Success Rate"),
            ("webhook_summary_rod", "Rod Name"),
            ("webhook_summary_config", "Active Config"),
            ("webhook_summary_totem_state", "Totem State"),
            ("webhook_summary_totem_pops", "Totem Pops"),
            ("webhook_summary_session_time", "Session Time"),
            ("webhook_summary_cast_timeouts", "Cast Timeouts"),
        ]

        for key, label in fields:
            switch = ctk.CTkSwitch(
                fields_frame, text=label,
                command=lambda k=key: self._toggle_field(k),
            )
            switch.pack(anchor="w", padx=15, pady=2)
            if self.app.main_settings.get(key, 0):
                switch.select()
            self.field_switches[key] = switch

        ctk.CTkLabel(fields_frame, text="").pack(pady=5)

        # === Alerts ===
        alerts_frame = ctk.CTkFrame(self, corner_radius=10)
        alerts_frame.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(
            alerts_frame, text="Alerts", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.totem_failed_switch = ctk.CTkSwitch(
            alerts_frame, text="Alert on Totem Failure",
            command=self._toggle_totem_alert,
        )
        self.totem_failed_switch.pack(anchor="w", padx=15, pady=(2, 10))
        if self.app.main_settings.get("webhook_alert_totem_failed", 0):
            self.totem_failed_switch.select()

        # Test button
        ctk.CTkButton(
            alerts_frame, text="Send Test Webhook", width=150, command=self._test_webhook
        ).pack(anchor="w", padx=15, pady=(0, 15))

    def _toggle_enabled(self):
        val = 1 if self.enabled_switch.get() else 0
        self.app.main_settings["webhook_enabled"] = val
        self.app.save_settings()

    def _save_url(self, event=None):
        self.app.main_settings["webhook_url"] = self.url_entry.get().strip()
        self.app.save_settings()

    def _save_interval(self, event=None):
        try:
            val = max(1, int(self.interval_entry.get().strip()))
            self.app.main_settings["webhook_summary_interval_min"] = val
            self.app.save_settings()
        except ValueError:
            pass

    def _toggle_field(self, key: str):
        switch = self.field_switches.get(key)
        if switch:
            self.app.main_settings[key] = 1 if switch.get() else 0
            self.app.save_settings()

    def _toggle_totem_alert(self):
        val = 1 if self.totem_failed_switch.get() else 0
        self.app.main_settings["webhook_alert_totem_failed"] = val
        self.app.save_settings()

    def _test_webhook(self):
        self.app.webhook.send_alert(
            "Test Notification",
            "OpenMacro XTernal Python edition is working correctly!"
        )
        messagebox.showinfo("Sent", "Test webhook sent!")
