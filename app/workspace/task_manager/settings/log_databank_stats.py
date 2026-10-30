"""Log databank stats settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Log databank stats"
    automation settings. Configures databank targeting and metrics selection.

Purpose:
    FEAT-TASK-MANAGER: Support databank statistics logging configuration workflows.

Key Capabilities:
    - FR-settings-log-databank-stats: Read and write LogDatabankStats configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.log_databank_stats import (
        LogDatabankStatsConfig,
        LogDatabankStatsSettings,
    )

    config = LogDatabankStatsSettings.load({"databank": "Results"})
    target = {}
    LogDatabankStatsSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["LogDatabankStatsConfig", "LogDatabankStatsSettings"]


@dataclass(frozen=True, slots=True)
class LogDatabankStatsConfig:
    """Immutable configuration for Log databank stats task."""

    databank: str = "Results"
    metrics: list[str] = field(
        default_factory=lambda: ["count", "netProfit", "sharpeRatio"]
    )
    log_level: str = "INFO"


class LogDatabankStatsSettings:
    """Serialization and deserialization helper for LogDatabankStats configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: LogDatabankStatsConfig | None = None,
    ) -> LogDatabankStatsConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else LogDatabankStatsConfig()

        base = current or LogDatabankStatsConfig()
        bank = str(payload.get("databank") or base.databank)

        raw_metrics = payload.get("metrics", base.metrics)
        if isinstance(raw_metrics, Sequence) and not isinstance(
            raw_metrics, (str, bytes)
        ):
            metrics = [str(m) for m in raw_metrics]
        elif isinstance(raw_metrics, str):
            metrics = [raw_metrics]
        else:
            metrics = list(base.metrics)

        level = str(
            payload.get("log_level") or payload.get("logLevel") or base.log_level
        )

        return LogDatabankStatsConfig(
            databank=bank,
            metrics=metrics,
            log_level=level,
        )

    @staticmethod
    def write(target: dict[str, Any], config: LogDatabankStatsConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["databank"] = config.databank
        target["metrics"] = list(config.metrics)
        target["logLevel"] = config.log_level

    @staticmethod
    def to_dict(config: LogDatabankStatsConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
