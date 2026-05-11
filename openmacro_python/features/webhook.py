"""
OpenMacro XTernal - Python Edition
Discord webhook notification system.
"""

import time
import json
import threading
import requests

from .fish import MacroState


class WebhookManager:
    """Manages Discord webhook notifications."""

    def __init__(self, settings: dict):
        self.settings = settings
        self.started_at: float = 0
        self.last_summary_at: float = 0

    def start_session(self):
        """Start tracking a new session."""
        if self.started_at == 0:
            self.started_at = time.time()
            self.last_summary_at = time.time()

    def reset_session(self):
        """Reset session tracking."""
        self.started_at = 0
        self.last_summary_at = 0

    def get_accent_color(self) -> int:
        """Get the configured accent color as an integer."""
        try:
            return int(self.settings.get("appearance", {}).get("accent_color", "5aa9ff"), 16)
        except (ValueError, TypeError):
            return 0x5AA9FF

    def send_summary(self, macro: MacroState, rod_name: str, config_name: str):
        """Send periodic summary webhook (called from macro loop)."""
        main = self.settings.get("main", self.settings)
        if not main.get("webhook_enabled"):
            return
        url = main.get("webhook_url", "")
        if not url:
            return
        if self.started_at == 0:
            return

        interval_min = max(1, int(main.get("webhook_summary_interval_min", 30)))
        interval_s = interval_min * 60

        if self.last_summary_at and (time.time() - self.last_summary_at) < interval_s:
            return

        payload = self._build_summary_payload(macro, rod_name, config_name, main)
        self._send_async(url, payload)
        self.last_summary_at = time.time()

    def send_alert(self, title: str, description: str, color: int = 0):
        """Send an instant alert webhook."""
        main = self.settings.get("main", self.settings)
        if not main.get("webhook_enabled"):
            return
        url = main.get("webhook_url", "")
        if not url:
            return

        if color == 0:
            color = self.get_accent_color()

        content = f"## {title}"
        if description:
            content += f"\n{description}"

        container = {
            "type": 17,
            "accent_color": color,
            "components": [{"type": 10, "content": content}],
        }
        payload = {"flags": 32768, "components": [container]}
        self._send_async(url, json.dumps(payload))

    def _build_summary_payload(
        self, macro: MacroState, rod_name: str, config_name: str, main: dict
    ) -> str:
        runtime_s = time.time() - self.started_at if self.started_at else 0

        header = "## XTernal Summary"
        if main.get("webhook_summary_session_time"):
            header += f"\n**Session runtime:** {self._format_runtime(runtime_s)}"

        stat_lines = []
        if main.get("webhook_summary_fish"):
            stat_lines.append(f"**Caught:** {macro.fish_caught_count}")
            stat_lines.append(f"**Lost:** {macro.fish_lost_count}")
        if main.get("webhook_summary_success_rate"):
            stat_lines.append(f"**Success Rate:** {macro.success_rate:.1f}%")
        if main.get("webhook_summary_cast_timeouts"):
            stat_lines.append(f"**Cast Timeouts:** {macro.cast_timeout_count}")
        if main.get("webhook_summary_totem_pops"):
            stat_lines.append(f"**Totems Popped:** {macro.totem_pop_count}")

        identity_lines = []
        if main.get("webhook_summary_rod"):
            identity_lines.append(f"**Rod:** {rod_name or '---'}")
        if main.get("webhook_summary_config"):
            identity_lines.append(f"**Config:** {config_name or '---'}")
        if main.get("webhook_summary_totem_state"):
            identity_lines.append(f"**Auto Totem:** {self._totem_state_text(main)}")

        components = [{"type": 10, "content": header}]
        if stat_lines:
            components.append({"type": 14})
            components.append({"type": 10, "content": "\n".join(stat_lines)})
        if identity_lines:
            components.append({"type": 14})
            components.append({"type": 10, "content": "\n".join(identity_lines)})

        container = {
            "type": 17,
            "accent_color": self.get_accent_color(),
            "components": components,
        }
        return json.dumps({"flags": 32768, "components": [container]})

    def _totem_state_text(self, main: dict) -> str:
        if not main.get("auto_totem_enabled"):
            return "Disabled"
        mode = main.get("auto_totem_mode", "expire")
        if mode == "interval":
            return f"Enabled (interval {main.get('auto_totem_interval_sec', 900)}s)"
        return "Enabled (on expire)"

    def _format_runtime(self, seconds: float) -> str:
        seconds = max(0, int(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        if minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"

    def _send_async(self, url: str, payload: str):
        """Send webhook in a background thread to avoid blocking."""
        def _post():
            try:
                requests.post(
                    f"{url}?with_components=true",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
            except Exception:
                pass

        threading.Thread(target=_post, daemon=True).start()
