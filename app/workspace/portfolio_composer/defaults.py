"""Portfolio Composer initial configuration defaults.

Description:
    Constructs the observed composition view's initial settings with injected
    date labels and default Markowitz model parameters.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-defaults: Construct initial configuration defaults.
Python API Usage:
    from app.workspace.portfolio_composer.defaults import (
        ComposerDefaults,
        ComposerViewDefaults,
    )
    defaults = ComposerDefaults.create(today_label="2026-11-01")
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer/test_defaults.py
"""

from __future__ import annotations

from typing import TypedDict

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class ComposerViewDefaults(TypedDict):
    """Observed Portfolio Composer initial view settings dictionary."""

    date_range: str
    start_day: str
    end_day: str
    initial_capital: int | float
    leverage: int
    results: list[object]
    weights: list[object]
    mm_methods: list[object]
    mm_methods_different: bool
    portfolio_name: str | None
    model_type: str
    selection_type: str
    max_simulations: int
    conf_level: int
    risk_free_rate: float
    req_std_dev: int | float


class ComposerDefaults:
    """Factory for constructing Portfolio Composer view default settings."""

    @staticmethod
    def create(*, today_label: str) -> ComposerViewDefaults:
        """Create a fresh dictionary of initial composition view settings.

        Args:
            today_label: Preformatted date label string for start and end dates.

        Returns:
            ComposerViewDefaults with standard initial parameters and fresh lists.

        Raises:
            TypeError: If today_label is not a string.
        """
        if not isinstance(today_label, str):
            raise TypeError("today_label must be a string")

        logger.info(
            "FR-composer-defaults: creating view defaults for today_label=%s",
            today_label,
        )

        return {
            "date_range": "full",
            "start_day": today_label,
            "end_day": today_label,
            "initial_capital": 100000,
            "leverage": 1,
            "results": [],
            "weights": [],
            "mm_methods": [],
            "mm_methods_different": False,
            "portfolio_name": None,
            "model_type": "markowitz",
            "selection_type": "SharpRatio",
            "max_simulations": 10,
            "conf_level": 95,
            "risk_free_rate": 0.7,
            "req_std_dev": -1,
        }
