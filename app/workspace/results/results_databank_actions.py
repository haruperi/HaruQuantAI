"""Databank toolbar actions and portfolio operations service.

Description:
    Implements ResultsDatabankActionsService handling databank operations
    including clearAll, delete, select, setNote, get/set parameters,
    portfolio merge/split, strategy comparison, and CSV export.

Purpose:
    FEAT-RESULTS-DATABANK-ACTIONS: Databank toolbar actions suite.

Key Capabilities:
    - FR-results-databank-actions: Databank mutation and portfolio merging.

Python API Usage:
    from app.workspace.results.results_databank_actions import (
        ResultsDatabankActionsService,
    )
    service = ResultsDatabankActionsService()
    receipt = service.delete_strategies("p1", "Results", ("S1",))

CLI Usage:
    python -m app.cli results databank delete --strategy-ids "S1,S2"
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, replace
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float

logger = get_logger(__name__)

MIN_PORTFOLIO_STRATEGIES = 2


@dataclass(frozen=True, slots=True)
class DatabankMutationReceipt:
    """Receipt summarizing databank modification action."""

    project_id: str
    databank_name: str
    affected_count: int
    strategy_ids: tuple[str, ...]
    action: str
    revision: int

    def to_dict(self) -> dict[str, Any]:
        """Convert mutation receipt to dictionary."""
        return {
            "project_id": self.project_id,
            "databank_name": self.databank_name,
            "affected_count": self.affected_count,
            "strategy_ids": list(self.strategy_ids),
            "action": self.action,
            "revision": self.revision,
        }


class ResultsDatabankActionsService:
    """Service executing databank toolbar and strategy management actions."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}
        self._databank_members: dict[str, set[str]] = {}
        self._revision: int = 1

    def register_in_memory_result(
        self, result: RunResult, databank_name: str = "Results"
    ) -> None:
        """Register candidate result in databank."""
        self._in_memory_results[result.strategy_id] = result
        self._databank_members.setdefault(databank_name, set()).add(result.strategy_id)

    def clear_all(self, project_id: str, databank_name: str) -> DatabankMutationReceipt:
        """Clear all strategies from the target databank."""
        members = self._databank_members.get(databank_name, set())
        affected = tuple(members)
        for sid in affected:
            self._in_memory_results.pop(sid, None)
        self._databank_members[databank_name] = set()
        self._revision += 1

        logger.info(
            "FR-results-databank-actions: cleared %d strategies from databank %s",
            len(affected),
            databank_name,
        )
        return DatabankMutationReceipt(
            project_id=project_id,
            databank_name=databank_name,
            affected_count=len(affected),
            strategy_ids=affected,
            action="CLEAR_ALL",
            revision=self._revision,
        )

    def delete_strategies(
        self,
        project_id: str,
        databank_name: str,
        strategy_ids: tuple[str, ...],
    ) -> DatabankMutationReceipt:
        """Delete specified strategy IDs from the target databank."""
        members = self._databank_members.setdefault(databank_name, set())
        deleted: list[str] = []

        for sid in strategy_ids:
            if sid in members or sid in self._in_memory_results:
                members.discard(sid)
                self._in_memory_results.pop(sid, None)
                deleted.append(sid)

        self._revision += 1
        logger.info(
            "FR-results-databank-actions: deleted %d strategies from databank %s",
            len(deleted),
            databank_name,
        )
        return DatabankMutationReceipt(
            project_id=project_id,
            databank_name=databank_name,
            affected_count=len(deleted),
            strategy_ids=tuple(deleted),
            action="DELETE",
            revision=self._revision,
        )

    def select_by_filter(
        self,
        project_id: str,
        databank_name: str,
        status: Literal["PASSED", "FAILED"],
    ) -> tuple[str, ...]:
        """Select strategy IDs matching pass/fail criteria."""
        logger.info(
            "FR-results-databank-actions: select_by_filter proj=%s db=%s status=%s",
            project_id,
            databank_name,
            status,
        )
        members = self._databank_members.get(databank_name, set())
        matched: list[str] = []

        for sid in sorted(members):
            res = self._in_memory_results.get(sid)
            if not res:
                continue
            # A strategy is considered PASSED if net_profit > 0 and drawdown >= -50%
            np = to_float(res.metrics.get("net_profit", 0.0))
            is_passed = np > 0.0
            if (status == "PASSED" and is_passed) or (
                status == "FAILED" and not is_passed
            ):
                matched.append(sid)

        return tuple(matched)

    def set_note(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        note: str,
    ) -> DatabankMutationReceipt:
        """Set user note on target strategy."""
        res = self._in_memory_results.get(strategy_id)
        if not res:
            raise DomainError(
                code="RESULTS_STRATEGY_NOT_FOUND",
                message=f"Strategy '{strategy_id}' not found",
                details={"strategy_id": strategy_id},
            )
        new_metrics = dict(res.metrics)
        new_metrics["note"] = note
        updated = replace(res, metrics=new_metrics)
        self._in_memory_results[strategy_id] = updated
        self._revision += 1

        logger.info(
            "FR-results-databank-actions: set note on strategy %s",
            strategy_id,
        )
        return DatabankMutationReceipt(
            project_id=project_id,
            databank_name=databank_name,
            affected_count=1,
            strategy_ids=(strategy_id,),
            action="SET_NOTE",
            revision=self._revision,
        )

    def get_strategy_parameters(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
    ) -> dict[str, str | int | float | bool]:
        """Get parameter key-value map for target strategy."""
        logger.info(
            "FR-results-databank-actions: get_params proj=%s db=%s strat=%s",
            project_id,
            databank_name,
            strategy_id,
        )
        res = self._in_memory_results.get(strategy_id)
        if not res:
            raise DomainError(
                code="RESULTS_STRATEGY_NOT_FOUND",
                message=f"Strategy '{strategy_id}' not found",
                details={"strategy_id": strategy_id},
            )
        out: dict[str, str | int | float | bool] = {}
        for k, v in res.parameters.items():
            if isinstance(v, (str, int, float, bool)):
                out[str(k)] = v
        return out

    def set_strategy_parameters(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        parameters: dict[str, Any],
    ) -> DatabankMutationReceipt:
        """Update parameter values on target strategy."""
        res = self._in_memory_results.get(strategy_id)
        if not res:
            raise DomainError(
                code="RESULTS_STRATEGY_NOT_FOUND",
                message=f"Strategy '{strategy_id}' not found",
                details={"strategy_id": strategy_id},
            )
        new_params = dict(res.parameters)
        new_params.update(parameters)
        updated = replace(res, parameters=new_params)
        self._in_memory_results[strategy_id] = updated
        self._revision += 1

        logger.info(
            "FR-results-databank-actions: updated parameters on %s",
            strategy_id,
        )
        return DatabankMutationReceipt(
            project_id=project_id,
            databank_name=databank_name,
            affected_count=1,
            strategy_ids=(strategy_id,),
            action="SET_PARAMETERS",
            revision=self._revision,
        )

    def merge_portfolio(
        self,
        project_id: str,
        databank_name: str,
        strategy_ids: tuple[str, ...],
        *,
        mode: Literal["STANDARD", "WF"] = "STANDARD",
    ) -> str:
        """Merge multiple strategies into a single portfolio strategy."""
        logger.info(
            "FR-results-databank-actions: merge proj=%s db=%s mode=%s count=%d",
            project_id,
            databank_name,
            mode,
            len(strategy_ids),
        )
        if len(strategy_ids) < MIN_PORTFOLIO_STRATEGIES:
            raise DomainError(
                code="RESULTS_PORTFOLIO_MIN_STRATEGIES",
                message=(
                    f"Portfolio merge requires at least {MIN_PORTFOLIO_STRATEGIES} "
                    f"strategies, got {len(strategy_ids)}"
                ),
                details={"strategy_ids": list(strategy_ids)},
            )

        combined_trades: list[dict[str, Any]] = []
        total_np = 0.0
        names: list[str] = []

        for sid in strategy_ids:
            res = self._in_memory_results.get(sid)
            if not res:
                raise DomainError(
                    code="RESULTS_STRATEGY_NOT_FOUND",
                    message=f"Strategy '{sid}' not found for portfolio merge",
                    details={"strategy_id": sid},
                )
            names.append(res.strategy_name)
            np = to_float(res.metrics.get("net_profit", 0.0))
            total_np += np
            combined_trades.extend(dict(t) for t in res.trades)

        portfolio_name = f"Portfolio({', '.join(names)})"
        portfolio_id = f"Portfolio_{'_'.join(strategy_ids)}"

        portfolio_result = RunResult(
            result_id=f"res_{portfolio_id}",
            databank_id=databank_name,
            strategy_id=portfolio_id,
            strategy_name=portfolio_name,
            metrics={"net_profit": round(total_np, 2)},
            trades=tuple(combined_trades),
            parameters={"constituent_strategy_ids": list(strategy_ids)},
        )
        self.register_in_memory_result(portfolio_result, databank_name)
        self._revision += 1

        logger.info(
            "FR-results-databank-actions: merged portfolio %s with net_profit=%.2f",
            portfolio_id,
            total_np,
        )
        return portfolio_id

    def split_portfolio(
        self,
        project_id: str,
        databank_name: str,
        portfolio_strategy_id: str,
    ) -> tuple[str, ...]:
        """Split a portfolio strategy restoring its constituent strategy IDs."""
        logger.info(
            "FR-results-databank-actions: split proj=%s db=%s portfolio=%s",
            project_id,
            databank_name,
            portfolio_strategy_id,
        )
        res = self._in_memory_results.get(portfolio_strategy_id)
        if not res:
            raise DomainError(
                code="RESULTS_STRATEGY_NOT_FOUND",
                message=f"Portfolio strategy '{portfolio_strategy_id}' not found",
                details={"strategy_id": portfolio_strategy_id},
            )

        constituents = res.parameters.get("constituent_strategy_ids", [])
        if not isinstance(constituents, (list, tuple)):
            return ()

        logger.info(
            "FR-results-databank-actions: split portfolio %s into %d strategies",
            portfolio_strategy_id,
            len(constituents),
        )
        return tuple(str(sid) for sid in constituents)

    def compare_strategies(
        self,
        project_id: str,
        databank_name: str,
        strategy_ids: tuple[str, ...],
    ) -> dict[str, dict[str, float | str]]:
        """Compare multiple strategies across key metric dimensions."""
        logger.info(
            "FR-results-databank-actions: compare proj=%s db=%s count=%d",
            project_id,
            databank_name,
            len(strategy_ids),
        )
        comparison: dict[str, dict[str, float | str]] = {}
        for sid in strategy_ids:
            res = self._in_memory_results.get(sid)
            if not res:
                continue
            strat_metrics: dict[str, float | str] = {
                "strategy_name": res.strategy_name,
                "net_profit": to_float(res.metrics.get("net_profit", 0.0)),
                "profit_factor": to_float(res.metrics.get("profit_factor", 0.0)),
                "trades_count": float(len(res.trades)),
            }
            comparison[sid] = strat_metrics
        return comparison

    def export_databank_csv(
        self,
        project_id: str,
        databank_name: str,
        column_ids: tuple[str, ...],
        *,
        separator: str = ",",
    ) -> str:
        """Export databank strategy rows to formatted CSV text."""
        logger.info(
            "FR-results-databank-actions: export_csv proj=%s db=%s cols=%d",
            project_id,
            databank_name,
            len(column_ids),
        )
        members = self._databank_members.get(databank_name, set())
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=separator, lineterminator="\n")

        # Write header
        writer.writerow(list(column_ids))

        # Write rows
        for sid in sorted(members):
            res = self._in_memory_results.get(sid)
            if not res:
                continue
            row_vals: list[str] = []
            for col in column_ids:
                if col in {"ResultsName", "Name"}:
                    row_vals.append(res.strategy_name)
                elif col in res.metrics:
                    row_vals.append(str(res.metrics[col]))
                else:
                    row_vals.append("")
            writer.writerow(row_vals)

        return buf.getvalue()
