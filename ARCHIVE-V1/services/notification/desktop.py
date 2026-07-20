"""Desktop notification service using powershell, osascript, or notify-send.

This module provides native desktop notification capabilities for Windows, macOS,
and Linux hosts.
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass

from .base import (
    BaseNotifier,
    NotificationMessage,
    NotificationResult,
    RateLimiter,
)


@dataclass
class DesktopConfig:
    """Configuration for Desktop notification service."""

    enabled: bool = True


class DesktopNotifier(BaseNotifier):
    """Desktop notification service using native OS commands."""

    def __init__(
        self,
        config: DesktopConfig,
        rate_limit: RateLimiter | None = None,
    ) -> None:
        """Initialize Desktop notifier.

        Args:
            config: Desktop configuration instance.
            rate_limit: Optional rate limiter instance.
        """
        super().__init__("DesktopNotifier", rate_limit)
        self.config = config

    def send(self, message: NotificationMessage) -> NotificationResult:
        """Send a native desktop notification to the host operating system.

        Args:
            message: The notification message to send.

        Returns:
            NotificationResult representing the outcome.
        """
        title = message.title
        body = message.body
        timeout_seconds = 5.0

        try:
            if sys.platform == "win32":
                # Windows: Run PowerShell for standard BalloonTip
                ps_script = (
                    "[void] [System.Reflection.Assembly]::"
                    "LoadWithPartialName('System.Windows.Forms'); "
                    "$notification = New-Object System.Windows.Forms.NotifyIcon; "
                    "$notification.Icon = [System.Drawing.SystemIcons]::Information; "
                    "$notification.BalloonTipIcon = 'Info'; "
                    f"$notification.BalloonTipTitle = {self._ps_quote(title)}; "
                    f"$notification.BalloonTipText = {self._ps_quote(body)}; "
                    "$notification.Visible = $True; "
                    "$notification.ShowBalloonTip(10000); "
                    "Start-Sleep -Seconds 1"
                )
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            elif sys.platform == "darwin":
                # macOS: AppleScript notification
                escaped_body = body.replace('"', '\\"')
                escaped_title = title.replace('"', '\\"')
                script = (
                    f'display notification "{escaped_body}" '
                    f'with title "{escaped_title}"'
                )
                subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            else:
                # Linux / Unix: notify-send
                subprocess.run(
                    ["notify-send", title, body],
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                )

            self.logger.info("Sent desktop notification successfully")
            return NotificationResult(
                success=True,
                message_id=f"desktop_{int(time.time())}",
                delivery_time_ms=0,
            )

        except subprocess.TimeoutExpired as e:
            self.logger.error("Desktop notification command timed out")
            return NotificationResult(
                success=False,
                error_message=f"Timeout expired: {e}",
            )
        except Exception as e:
            self.logger.exception("Failed to send desktop notification")
            return NotificationResult(success=False, error_message=str(e))

    def _ps_quote(self, s: str) -> str:
        """Escape and single-quote a string for PowerShell.

        Args:
            s: Raw string to quote.

        Returns:
            Single-quoted PowerShell literal.
        """
        escaped = s.replace("'", "''")
        return f"'{escaped}'"

    def test_connection(self) -> bool:
        """Test desktop notification connection.

        Returns:
            Always returns True as it is a local service.
        """
        return True
