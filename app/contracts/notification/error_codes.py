# ruff: noqa: N801, N816, RUF022, RUF100  # Exact public names/order.
"""Generated MQL5-based contract vocabulary. DO NOT EDIT."""

from __future__ import annotations

from typing import Final

ERR_MAIL_SEND_FAILED: Final[int] = 4510
ERR_NOTIFICATION_SEND_FAILED: Final[int] = 4515
ERR_NOTIFICATION_WRONG_PARAMETER: Final[int] = 4516
ERR_NOTIFICATION_WRONG_SETTINGS: Final[int] = 4517
ERR_NOTIFICATION_TOO_FREQUENT: Final[int] = 4518

__all__ = [
    "ERR_MAIL_SEND_FAILED",
    "ERR_NOTIFICATION_SEND_FAILED",
    "ERR_NOTIFICATION_TOO_FREQUENT",
    "ERR_NOTIFICATION_WRONG_PARAMETER",
    "ERR_NOTIFICATION_WRONG_SETTINGS",
]
