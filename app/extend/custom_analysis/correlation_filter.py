"""Custom analysis snippet: CorrelationFilter (matching donor CorrelationFilter.java).

Description:
    Implements CorrelationFilter custom analysis method extending
    CustomAnalysisMethod (TYPE_PROCESS_DATABANK). Sorts databank strategies
    descending by fitness and removes any subordinate strategy whose pairwise
    ProfitLoss correlation with a higher-fitness strategy exceeds maxCorrelation.

Purpose:
    FEAT-EXTEND-CUSTOM-ANALYSIS: Databank correlation filtering custom analysis snippet.

Key Capabilities:
    - FR-custom-analysis-correlation-filter: Prune correlated databank strategies.
    - FR-custom-analysis-precompute-periods: Precompute ProfitLoss period buckets.

Python API Usage:
    from app.extend.custom_analysis.correlation_filter import CorrelationFilter
    from app.extend.custom_analysis.base import ResultsGroup

    cf = CorrelationFilter()
    cf.set_input_args("0.5")
    pruned = cf.process_databank("Project1", "Task1", "Results", [rg1, rg2])

CLI Usage:
    uv run python -m pytest tests/extend/test_custom_analysis.py
"""

from __future__ import annotations

from typing import Literal, override

from app.core.host.logging import get_logger
from app.extend.correlation_of.base import CorrelationOrderRecord
from app.extend.correlation_of.catalog import CorrelationOfCatalog
from app.extend.custom_analysis.base import (
    TYPE_PROCESS_DATABANK,
    CustomAnalysisMethod,
    ResultsGroup,
)

logger = get_logger(__name__)

CorrelationPeriod = Literal["HOUR", "DAY", "WEEK", "MONTH", "YEAR"]
_DAY_MS: int = 86_400_000
_HOUR_MS: int = 3_600_000
_DEFAULT_MAX_CORRELATION: float = 0.5


class CorrelationFilter(CustomAnalysisMethod):
    """Custom analysis method for filtering correlated strategies in a databank."""

    def __init__(self) -> None:
        """Initialize CorrelationFilter with TYPE_PROCESS_DATABANK."""
        super().__init__("CorrelationFilter", TYPE_PROCESS_DATABANK)

    @override
    def filter_strategy(
        self,
        project: str,
        task: str,
        databank_name: str,
        rg: ResultsGroup,
    ) -> bool:
        """Always return True for single-strategy pass.

        Args:
            project: Project name.
            task: Task name.
            databank_name: Databank name.
            rg: ResultsGroup instance.

        Returns:
            Always True as CorrelationFilter operates on databanks.
        """
        logger.debug(
            "FR-custom-analysis-correlation-filter: filter on %s in %s/%s/%s",
            rg.get_name(),
            project,
            task,
            databank_name,
        )
        return True

    @override
    def process_databank(
        self,
        project_name: str,
        task: str,
        databank_name: str,
        databank_rg: list[ResultsGroup],
    ) -> list[ResultsGroup]:
        """Prune correlated strategies in databank ordered by fitness descending.

        Args:
            project_name: Project name.
            task: Task name.
            databank_name: Databank name.
            databank_rg: Input list of ResultsGroup strategies.

        Returns:
            Pruned list of ResultsGroup strategies with correlation <= max_correlation.
        """
        logger.info(
            "FR-custom-analysis-correlation-filter: databank '%s' "
            "(project=%s, task=%s) with %d strategies",
            databank_name,
            project_name,
            task,
            len(databank_rg),
        )
        if not databank_rg:
            return []

        raw_args = self.get_input_args().strip()
        max_correlation: float = (
            float(raw_args) if raw_args else _DEFAULT_MAX_CORRELATION
        )

        # Clone source records
        rg_target: list[ResultsGroup] = [rg.clone() for rg in databank_rg]

        # Order results by fitness descending
        rg_target.sort(key=lambda item: item.get_fitness(), reverse=True)

        i = 0
        while i < len(rg_target):
            focus_strat = rg_target[i].clone()
            focus_strat_name = focus_strat.get_name()

            j = i + 1
            while j < len(rg_target):
                sub_strat = rg_target[j].clone()
                sub_strat_name = sub_strat.get_name()

                corr_value = round(
                    self.compute_strategy_correlation(focus_strat, sub_strat), 2
                )

                if corr_value > max_correlation:
                    logger.debug(
                        "FR-custom-analysis-correlation-filter: removing %s "
                        "(corr=%.2f > %.2f with %s)",
                        sub_strat_name,
                        corr_value,
                        max_correlation,
                        focus_strat_name,
                    )
                    rg_target.pop(j)
                else:
                    j += 1
            i += 1

        return rg_target

    def compute_strategy_correlation(
        self,
        rg1: ResultsGroup,
        rg2: ResultsGroup,
        period: CorrelationPeriod = "DAY",
    ) -> float:
        """Compute pairwise ProfitLoss correlation between two ResultsGroup instances.

        Args:
            rg1: Focus strategy ResultsGroup.
            rg2: Subordinate strategy ResultsGroup.
            period: Temporal bucketing period (default DAY).

        Returns:
            Pearson correlation rounded to 4 decimals, or 0.0 if empty/undefined.
        """
        p1, p2 = self.precompute_periods_ap(rg1, rg2, period)
        if not p1 or not p2:
            return 0.0
        return CorrelationOfCatalog.pearson(
            "ProfitLoss", p1, p2, allow_empty_periods=True
        )

    def precompute_periods_ap(
        self,
        rg1: ResultsGroup,
        rg2: ResultsGroup,
        period: CorrelationPeriod = "DAY",
    ) -> tuple[dict[int, float], dict[int, float]]:
        """Precompute ProfitLoss period buckets for two strategies.

        Args:
            rg1: First ResultsGroup.
            rg2: Second ResultsGroup.
            period: Aggregation period (default DAY).

        Returns:
            Tuple of (buckets_rg1, buckets_rg2).
        """
        records1 = self._to_correlation_records(rg1)
        records2 = self._to_correlation_records(rg2)

        p1 = (
            CorrelationOfCatalog.compute_periods("ProfitLoss", records1, period=period)
            if records1
            else {}
        )
        p2 = (
            CorrelationOfCatalog.compute_periods("ProfitLoss", records2, period=period)
            if records2
            else {}
        )
        return p1, p2

    @staticmethod
    def _to_correlation_records(
        rg: ResultsGroup,
    ) -> list[CorrelationOrderRecord]:
        """Convert ResultsGroup orders to CorrelationOrderRecord list."""
        records: list[CorrelationOrderRecord] = []
        for idx, o in enumerate(rg.orders()):
            if o.is_balance_order():
                continue
            close_time = o.close_time_ms if o.close_time_ms > 0 else (idx + 1) * _DAY_MS
            open_time = (
                o.open_time_ms if o.open_time_ms > 0 else max(0, close_time - _HOUR_MS)
            )
            records.append(
                CorrelationOrderRecord(
                    open_time_ms=open_time,
                    close_time_ms=close_time,
                    profit_loss=o.pl,
                    is_canceled=False,
                    is_open_position=False,
                    is_long=o.direction >= 0,
                )
            )
        return records
