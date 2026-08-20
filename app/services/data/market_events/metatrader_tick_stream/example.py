"""Executable usage example for MT5 tick stream provider."""

# ruff: noqa: E402
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.kernel.effects import EffectScope
from app.services.data.market_events.metatrader_tick_stream.plugin import (
    create_provider,
)


def main() -> None:
    """Demonstrate MT5 tick stream provider initialization without credentials."""
    environment = os.getenv("ENVIRONMENT", "dev")
    account_mode = os.getenv("ACCOUNT_MODE", "simulation")

    if environment != "dev" or account_mode != "demo":
        print("MT5 smoke disabled")
        return

    scope = EffectScope()
    provider = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 256},
        scope=scope,
    )
    print(f"data.tick_stream.metatrader: active={provider.active}")
    scope.close()


if __name__ == "__main__":
    main()
