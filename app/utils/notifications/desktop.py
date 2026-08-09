"""OS-native desktop notification delivery."""

from __future__ import annotations

import base64
import platform
import subprocess
from dataclasses import dataclass
from typing import Protocol

from app.utils.errors.exceptions import ConfigurationError

_MAX_TITLE_LENGTH = 128
_MAX_MESSAGE_LENGTH = 1024
_MIN_TIMEOUT_SECONDS = 0.1
_MAX_TIMEOUT_SECONDS = 30.0


class _Runner(Protocol):
    """Callable subprocess boundary used by the desktop notifier."""

    def __call__(
        self,
        args: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True, slots=True)
class DesktopConfig:
    """Validated internal desktop notification configuration."""

    enabled: bool = False
    timeout_seconds: float = 5.0


class DesktopNotifier:
    """Deliver bounded messages through the current OS notification command."""

    def __init__(self, config: DesktopConfig, runner: _Runner = subprocess.run) -> None:
        self._config = config
        self._runner = runner

    @property
    def active(self) -> bool:
        """Return whether desktop delivery is enabled and supported."""
        return self._config.enabled and platform.system() in {
            "Windows",
            "Darwin",
            "Linux",
        }

    def send(
        self, title: str, message: str, _html_body: str | None = None
    ) -> dict[str, object]:
        """Deliver one desktop notification.

        Args:
            title: Bounded notification title.
            message: Bounded notification body.

        Returns:
            Secret-safe channel delivery result.

        Raises:
            ConfigurationError: If disabled, unsupported, invalid, or delivery fails.
        """
        if not self.active:
            raise ConfigurationError("NOTIFICATION_CHANNEL_UNAVAILABLE")
        command = _desktop_command(platform.system(), title, message)
        try:
            completed = self._runner(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise ConfigurationError("NOTIFICATION_DELIVERY_FAILED") from error
        if completed.returncode != 0:
            raise ConfigurationError("NOTIFICATION_DELIVERY_FAILED")
        return {"channel": "desktop", "status": "accepted"}


def _desktop_command(system: str, title: str, message: str) -> list[str]:
    """Build one injection-safe platform command.

    Args:
        system: Supported operating-system name.
        title: Notification title.
        message: Notification body.

    Returns:
        Platform command arguments.

    Raises:
        ConfigurationError: If content or the operating system is unsupported.
    """
    if (
        not title.strip()
        or not message.strip()
        or len(title) > _MAX_TITLE_LENGTH
        or len(message) > _MAX_MESSAGE_LENGTH
    ):
        raise ConfigurationError("NOTIFICATION_CONTENT_INVALID")
    if system == "Windows":
        encoded_title = base64.b64encode(title.encode()).decode("ascii")
        encoded_message = base64.b64encode(message.encode()).decode("ascii")
        script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "Add-Type -AssemblyName System.Drawing;"
            f"$t=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_title}'));"
            f"$m=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_message}'));"
            "$n=New-Object System.Windows.Forms.NotifyIcon;"
            "$n.Icon=[System.Drawing.SystemIcons]::Information;"
            "$n.Visible=$true;$n.ShowBalloonTip(5000,$t,$m,'Info');"
            "Start-Sleep -Seconds 1;$n.Dispose()"
        )
        return ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]
    if system == "Darwin":
        script = (
            "on run argv\n"
            "display notification (item 2 of argv) with title (item 1 of argv)\n"
            "end run"
        )
        return ["osascript", "-e", script, title, message]
    if system == "Linux":
        return ["notify-send", "--", title, message]
    raise ConfigurationError("NOTIFICATION_CHANNEL_UNAVAILABLE")


def build_desktop_notification_config(
    *, enabled: bool = False, timeout_seconds: float = 5.0
) -> object:
    """Build validated desktop notification configuration.

    Args:
        enabled: Whether desktop delivery is active.
        timeout_seconds: External command timeout.

    Returns:
        Opaque immutable desktop configuration.

    Raises:
        ConfigurationError: If the timeout is outside the supported range.
    """
    if not _MIN_TIMEOUT_SECONDS <= timeout_seconds <= _MAX_TIMEOUT_SECONDS:
        raise ConfigurationError("NOTIFICATION_CONFIG_INVALID")
    return DesktopConfig(enabled=enabled, timeout_seconds=timeout_seconds)


__all__ = ("build_desktop_notification_config",)
