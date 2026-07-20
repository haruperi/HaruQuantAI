"""Periodic portfolio optimization tools.

Purpose:
    Provide periodic portfolio weight optimization helpers and plotting for
    optimization workflows.

Classes and functions:
    PortfolioOptimizerResult: Class. Holds periodic portfolio weights.
    pfo_from_optimize_func: Function. Build periodic portfolio weights.
    pfo_plot: Function. Plot periodic portfolio optimizer weights.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd


class PortfolioOptimizerResult:
    """Hold periodic portfolio weights and plotting behavior."""

    def __init__(self, weights: pd.DataFrame) -> None:
        """Initialize a portfolio optimizer result."""
        self.weights = weights

    def plot(self) -> Any:
        """Plot portfolio weights over time.

        Purpose:
            Visualize periodic allocation weights.

        Tool class:
            read_only

        Risk level:
            low

        Approval required:
            none

        Side effects:
            Creates a matplotlib axis object.
        """
        import matplotlib.pyplot as plt

        try:
            if (self.weights < 0).any().any():
                ax = self.weights.plot(
                    kind="line",
                    figsize=(12, 6),
                    marker="o",
                    alpha=0.8,
                )
            else:
                ax = self.weights.plot(
                    kind="area",
                    stacked=True,
                    figsize=(12, 6),
                    alpha=0.8,
                )

            ax.set_title("Portfolio Allocation Over Time")
            ax.set_ylabel("Weights")
            ax.set_xlabel("Date")
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
            ax.axhline(0, color="black", lw=1, ls="--")
            plt.tight_layout()
            return ax
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"Plotting error: {exc}")
            return None


def pfo_from_optimize_func(
    data: Any,
    optimize_func: Callable[[Any], Any],
    every: str = "M",
) -> PortfolioOptimizerResult:
    """Periodically optimize portfolio weights from a callback.

    Purpose:
        Build periodic allocation weights from a deterministic optimization
        callback.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.
    """
    from app.services.data.frames import Data

    if not hasattr(data, "df"):
        raise ValueError("Data must be a HaruQuant Data object.")

    freq = {"M": "ME", "Y": "YE", "H": "h"}.get(every, every)
    all_weights: list[dict[str, Any]] = []
    for timestamp, group_df in data.df.groupby(pd.Grouper(freq=freq)):
        if group_df.empty:
            continue

        slice_data = Data(group_df)
        weights = optimize_func(slice_data)
        if isinstance(weights, pd.Series):
            row = weights.to_dict()
        elif isinstance(weights, dict):
            row = weights
        else:
            row = dict(zip(data.symbols, weights, strict=False))

        row["timestamp"] = timestamp
        all_weights.append(row)

    weights_df = pd.DataFrame(all_weights).set_index("timestamp")
    return PortfolioOptimizerResult(weights_df)


def pfo_plot(portfolio_optimizer: PortfolioOptimizerResult) -> Any:
    """Plot a portfolio optimizer result.

    Purpose:
        Render periodic allocation weights for inspection.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        Creates a matplotlib axis object.
    """
    return portfolio_optimizer.plot()


__all__ = ["PortfolioOptimizerResult", "pfo_from_optimize_func", "pfo_plot"]
