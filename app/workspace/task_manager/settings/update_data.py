"""Update data settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Update data"
    automation settings. Configures instruments, timeframes, and data providers.

Purpose:
    FEAT-TASK-MANAGER: Support market data update task configuration workflows.

Key Capabilities:
    - FR-settings-update-data: Read and write UpdateData configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.update_data import (
        UpdateDataConfig,
        UpdateDataSettings,
    )

    config = UpdateDataSettings.load({"symbol": "EURUSD", "timeframe": "M1"})
    target = {}
    UpdateDataSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["UpdateDataConfig", "UpdateDataSettings"]


@dataclass(frozen=True, slots=True)
class UpdateDataConfig:
    """Immutable configuration for Update data task."""

    symbol: str = "EURUSD"
    timeframe: str = "H1"
    data_provider: str = "Default"
    clean_history: bool = False


class UpdateDataSettings:
    """Serialization and deserialization helper for UpdateData configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: UpdateDataConfig | None = None,
    ) -> UpdateDataConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else UpdateDataConfig()

        base = current or UpdateDataConfig()
        sym = str(payload.get("symbol") or payload.get("instrument") or base.symbol)
        tf = str(payload.get("timeframe") or base.timeframe)
        provider = str(
            payload.get("data_provider")
            or payload.get("dataProvider")
            or payload.get("dataSource")
            or base.data_provider
        )
        clean = bool(
            payload.get("clean_history")
            if "clean_history" in payload
            else payload.get("cleanHistory", base.clean_history)
        )

        return UpdateDataConfig(
            symbol=sym,
            timeframe=tf,
            data_provider=provider,
            clean_history=clean,
        )

    @staticmethod
    def write(target: dict[str, Any], config: UpdateDataConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["symbol"] = config.symbol
        target["timeframe"] = config.timeframe
        target["dataProvider"] = config.data_provider
        target["cleanHistory"] = config.clean_history

    @staticmethod
    def to_dict(config: UpdateDataConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
