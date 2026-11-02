"""Custom analysis snippet: OutlierTrade (matching donor OutlierTrade.java).

Description:
    Implements OutlierTrade custom analysis method extending
    CustomAnalysisMethod (TYPE_FILTER_STRATEGY). Evaluates in-sample trades of a
    strategy and rejects strategies where the single largest trade profit exceeds
    the OutlierCoefficient times the sum of the second and third largest trade
    profits, with options to include or filter duplicate profit values.

Purpose:
    FEAT-EXTEND-CUSTOM-ANALYSIS: Outlier trade detection custom analysis snippet.

Key Capabilities:
    - FR-custom-analysis-outlier-trade: Outlier trade filtering CustomAnalysisMethod.
    - FR-custom-analysis-outlier-filter: Top-3 trade profit ratio threshold validation.

Python API Usage:
    from app.extend.custom_analysis.outlier_trade import OutlierTrade
    from app.extend.custom_analysis.base import ResultsGroup, CustomAnalysisOrder

    ot = OutlierTrade()
    ot.set_input_args("1.1, 1")
    passed = ot.filter_strategy("Project1", "Task1", "Results", rg)

CLI Usage:
    uv run python -m pytest tests/extend/test_custom_analysis.py
"""

from __future__ import annotations

from typing import override

from app.core.host.logging import get_logger
from app.extend.custom_analysis.base import (
    TYPE_FILTER_STRATEGY,
    CustomAnalysisMethod,
    OrdersList,
    ResultsGroup,
)

logger = get_logger(__name__)

MIN_TRADES_FOR_OUTLIER: int = 2
_EXPECTED_PARTS_COUNT: int = 2


def _update_top_three_unfiltered(
    pl: float, first: float, second: float, third: float
) -> tuple[float, float, float]:
    """Update top three profit values allowing duplicate profits."""
    if pl > first:
        return pl, first, second
    if pl > second:
        return first, pl, second
    if pl > third:
        return first, second, pl
    return first, second, third


def _update_top_three_filtered(
    pl: float, first: float, second: float, third: float
) -> tuple[float, float, float]:
    """Update top three profit values requiring distinct profit values."""
    if pl > first:
        return pl, first, second
    if pl > second and pl != first:
        return first, pl, second
    if pl > third and pl not in (first, second):
        return first, second, pl
    return first, second, third


class OutlierTrade(CustomAnalysisMethod):
    """Custom analysis method for filtering strategies dominated by an outlier trade."""

    def __init__(self) -> None:
        """Initialize OutlierTrade with TYPE_FILTER_STRATEGY."""
        super().__init__("OutlierTrade", TYPE_FILTER_STRATEGY)

    @override
    def filter_strategy(
        self,
        project: str,
        task: str,
        databank_name: str,
        rg: ResultsGroup,
    ) -> bool:
        """Filter strategy by outlier trade ratio against 2nd and 3rd largest profits.

        Input arguments format: "<outlier_coefficient>, <option>"
            - outlier_coefficient: e.g. 1.1
            - option: 0 (without filtering same PL) or 1 (filtering same PL)

        Args:
            project: Project name.
            task: Task name.
            databank_name: Databank name.
            rg: ResultsGroup strategy result instance.

        Returns:
            True if strategy passes outlier test; False if rejected or on error.
        """
        logger.info(
            "FR-custom-analysis-outlier-trade: evaluating strategy %s in %s/%s/%s",
            rg.get_name(),
            project,
            task,
            databank_name,
        )
        input_args = self.get_input_args().strip()

        try:
            parts = input_args.split(",")
            if len(parts) < _EXPECTED_PARTS_COUNT:
                logger.error(
                    "FR-custom-analysis-outlier-trade: invalid inputArgs '%s', "
                    "expected '<coefficient>, <option>'",
                    input_args,
                )
                return False

            outlier_coefficient = float(parts[0].strip())
            option = int(parts[1].strip())

            orders = rg.orders().filter_with_clone(
                rg.get_main_result_key(), direction=0, sample_type="InSample"
            )

            if orders.size() == 0:
                logger.debug(
                    "FR-custom-analysis-outlier-trade: strategy %s has "
                    "no in-sample orders",
                    rg.get_name(),
                )
                return False

            first_pl, second_pl, third_pl, count = self._compute_top_three(
                orders, option
            )

            if count > MIN_TRADES_FOR_OUTLIER:
                threshold = outlier_coefficient * (second_pl + third_pl)
                if first_pl > threshold:
                    logger.debug(
                        "FR-custom-analysis-outlier-trade: Biggest Order PL: "
                        "%f > %f + %f",
                        first_pl,
                        second_pl,
                        third_pl,
                    )
                    return False

            return True

        except ValueError, IndexError, AttributeError:
            logger.exception(
                "FR-custom-analysis-outlier-trade: Error OutlierTrade on %s",
                rg.get_name(),
            )
            return False

    @staticmethod
    def _compute_top_three(
        orders: OrdersList, option: int
    ) -> tuple[float, float, float, int]:
        """Iterate orders and extract top three profits and valid trade count."""
        first_pl: float = 0.0
        second_pl: float = 0.0
        third_pl: float = 0.0
        count: int = 0

        for i in range(orders.size()):
            order = orders.get(i)
            if order.is_balance_order():
                continue

            pl = order.pl
            if option == 0:
                first_pl, second_pl, third_pl = _update_top_three_unfiltered(
                    pl, first_pl, second_pl, third_pl
                )
            elif option == 1:
                first_pl, second_pl, third_pl = _update_top_three_filtered(
                    pl, first_pl, second_pl, third_pl
                )

            count += 1

        return first_pl, second_pl, third_pl, count
