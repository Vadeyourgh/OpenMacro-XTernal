"""
OpenMacro XTernal - Python Edition
About/Credits tab.
"""

import webbrowser
import customtkinter as ctk

from ...core.constants import FULL_VER


class AboutTab(ctk.CTkFrame):
    """About and Credits tab."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # === Changelog ===
        changelog_frame = ctk.CTkFrame(self, corner_radius=10)
        changelog_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            changelog_frame,
            text=f"Changelog - {FULL_VER}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(10, 5))

        changelog = (
            "- Ported to Python with modern CustomTkinter GUI\n"
            "- Fixed Appraisal bugs\n"
            "- Fixed Appraisal breaking fishing\n"
            "- Added Hotkeys for appraisal\n"
            "- Added Support for Tranquility Rod\n"
            "- Improved PD controller performance"
        )

        ctk.CTkLabel(
            changelog_frame,
            text=changelog,
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=350,
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # === Credits ===
        credits_frame = ctk.CTkFrame(self, corner_radius=10)
        credits_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            credits_frame,
            text="Credits",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            credits_frame,
            text="OpenMacro XTernal",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(5, 0))

        ctk.CTkLabel(
            credits_frame,
            text="Designed, developed & maintained by Misery",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=15, pady=2)

        ctk.CTkLabel(
            credits_frame,
            text="Python port with modern GUI",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=2)

        # Links
        link_row = ctk.CTkFrame(credits_frame, fg_color="transparent")
        link_row.pack(fill="x", padx=15, pady=(10, 15))

        discord_btn = ctk.CTkButton(
            link_row,
            text="Discord Server",
            width=130,
            command=lambda: webbrowser.open("https://discord.gg/d2gqxEUx7U"),
        )
        discord_btn.pack(side="left", padx=(0, 10))

        github_btn = ctk.CTkButton(
            link_row,
            text="GitHub Repo",
            width=130,
            fg_color="gray30",
            command=lambda: webbrowser.open(
                f"https://github.com/{self.app.settings.get('github_owner', 'termx3')}/OpenMacro-XTernal"
            ),
        )
        github_btn.pack(side="left")

        # Footer
        ctk.CTkLabel(
            self,
            text=f"OpenMacro XTernal {FULL_VER} | 2026 Misery. All rights reserved.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        ).pack(side="bottom", pady=10)
