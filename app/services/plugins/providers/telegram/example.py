"""Executable usage example for telegram notification delivery provider."""

# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.kernel.effects import EffectScope
from app.utils.notifications.providers.telegram.plugin import (  # type: ignore[import-untyped]
    create_provider,
)
from app.utils.notifications.telegram import (  # type: ignore[import-untyped]
    build_telegram_notification_config,
)


def main() -> None:
    """Demonstrate Telegram notification provider initialization without I/O."""
    config = build_telegram_notification_config(
        bot_token="dummy_bot_token",  # noqa: S106
        chat_ids=("12345678",),
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
