"""Executable usage example for email notification delivery provider."""

# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.kernel.effects import EffectScope
from app.utils.notifications.email import build_email_notification_config
from app.utils.notifications.providers.email.plugin import create_provider


def main() -> None:
    """Demonstrate email notification provider initialization without I/O."""
    config = build_email_notification_config(
        host="smtp.example.com",
        port=587,
        sender="noreply@example.com",
        recipients=("alerts@example.com",),
        enabled=False,
    )
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"configuration": config},
        scope=scope,
    )
    print(f"{adapter.channel}: active={adapter.active}")
    scope.close()


if __name__ == "__main__":
    main()
