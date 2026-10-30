"""Automatic portfolio builder settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Automatic Portfolio
    Builder" automation settings. Configures databank source/target, target portfolio
    size, correlation constraints, and strategy ranking methods.

Purpose:
    FEAT-TASK-MANAGER: Support portfolio builder task configuration workflows.

Key Capabilities:
    - FR-settings-auto-portfolio-builder: Read and write AutoPortfolioBuilder
      configuration dictionaries with validation and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.automatic_portfolio_builder import (
        AutoPortfolioBuilderConfig,
        AutoPortfolioBuilderSettings,
    )

    config = AutoPortfolioBuilderSettings.load({"portfolioSize": 10})
    target = {}
    AutoPortfolioBuilderSettings.write(target, config)
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

__all__ = ["AutoPortfolioBuilderConfig", "AutoPortfolioBuilderSettings"]


@dataclass(frozen=True, slots=True)
class AutoPortfolioBuilderConfig:
    """Immutable configuration for Automatic Portfolio Builder task."""

    source_databank: str = "Results"
    target_databank: str = "Portfolio"
    portfolio_size: int = 5
    correlation_threshold: float = 0.7
    ranking_method: str = "SharpeRatio"


class AutoPortfolioBuilderSettings:
    """Serialization helper for AutoPortfolioBuilder configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: AutoPortfolioBuilderConfig | None = None,
    ) -> AutoPortfolioBuilderConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else AutoPortfolioBuilderConfig()

        base = current or AutoPortfolioBuilderConfig()
        source_bank = str(
            payload.get("source_databank")
            or payload.get("sourceDatabank")
            or base.source_databank
        )
        target_bank = str(
            payload.get("target_databank")
            or payload.get("targetDatabank")
            or base.target_databank
        )
        p_size = int(
            payload.get("portfolio_size")
            or payload.get("portfolioSize")
            or base.portfolio_size
        )
        corr = float(
            payload.get("correlation_threshold")
            or payload.get("correlationThreshold")
            or base.correlation_threshold
        )
        ranking = str(
            payload.get("ranking_method")
            or payload.get("rankingMethod")
            or base.ranking_method
        )

        return AutoPortfolioBuilderConfig(
            source_databank=source_bank,
            target_databank=target_bank,
            portfolio_size=p_size,
            correlation_threshold=corr,
            ranking_method=ranking,
        )

    @staticmethod
    def write(target: dict[str, Any], config: AutoPortfolioBuilderConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["sourceDatabank"] = config.source_databank
        target["targetDatabank"] = config.target_databank
        target["portfolioSize"] = config.portfolio_size
        target["correlationThreshold"] = config.correlation_threshold
        target["rankingMethod"] = config.ranking_method

    @staticmethod
    def to_dict(config: AutoPortfolioBuilderConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
