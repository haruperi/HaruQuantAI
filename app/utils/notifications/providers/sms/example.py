"""Executable usage example for sms notification delivery provider."""

# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.kernel.effects import EffectScope
from app.utils.notifications.providers.sms.plugin import create_provider
from app.utils.notifications.sms import build_sms_notification_config


def main() -> None:
    """Demonstrate SMS notification provider initialization without I/O."""
    config = build_sms_notification_config(
        account_sid="AC00000000000000000000000000000000",  # pragma: allowlist secret
        auth_token="dummy_token",  # noqa: S106
        from_phone="+15550001",
        recipients=("+15550002",),
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
