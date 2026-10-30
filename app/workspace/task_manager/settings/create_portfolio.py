"""Create portfolio settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Create Portfolio"
    automation settings. Configures databank source, output portfolio name, and
    selection modes.

Purpose:
    FEAT-TASK-MANAGER: Support portfolio creation task settings serialization.

Key Capabilities:
    - FR-settings-create-portfolio: Read and write CreatePortfolio configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.create_portfolio import (
        CreatePortfolioConfig,
        CreatePortfolioSettings,
    )

    config = CreatePortfolioSettings.load({"portfolioName": "MasterPortfolio"})
    target = {}
    CreatePortfolioSettings.write(target, config)
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

__all__ = ["CreatePortfolioConfig", "CreatePortfolioSettings"]


@dataclass(frozen=True, slots=True)
class CreatePortfolioConfig:
    """Immutable configuration for Create Portfolio task."""

    source_databank: str = "Results"
    portfolio_name: str = "MyPortfolio"
    selection_mode: str = "all"
    top_n: int = 10


class CreatePortfolioSettings:
    """Serialization and deserialization helper for CreatePortfolio configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: CreatePortfolioConfig | None = None,
    ) -> CreatePortfolioConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else CreatePortfolioConfig()

        base = current or CreatePortfolioConfig()
        bank = str(
            payload.get("source_databank")
            or payload.get("sourceDatabank")
            or base.source_databank
        )
        name = str(
            payload.get("portfolio_name")
            or payload.get("portfolioName")
            or base.portfolio_name
        )
        mode = str(
            payload.get("selection_mode")
            or payload.get("selectionMode")
            or base.selection_mode
        )
        top = int(payload.get("top_n") or payload.get("topN") or base.top_n)

        return CreatePortfolioConfig(
            source_databank=bank,
            portfolio_name=name,
            selection_mode=mode,
            top_n=top,
        )

    @staticmethod
    def write(target: dict[str, Any], config: CreatePortfolioConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["sourceDatabank"] = config.source_databank
        target["portfolioName"] = config.portfolio_name
        target["selectionMode"] = config.selection_mode
        target["topN"] = config.top_n

    @staticmethod
    def to_dict(config: CreatePortfolioConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
