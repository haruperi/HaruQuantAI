"""Results workspace shell and result-key projection service.

Description:
    Implements AppResultsService managing strategy result selection,
    active tab routing, and project/getDataItems result-key projection
    over ResultStore and databank containers.

Purpose:
    FEAT-RESULTS-WORKSPACE-SHELL: Provide root strategy result projection.

Key Capabilities:
    - FR-results-selection-state: Project selection state and data items
      with Main, Portfolio, and sub-result keys in deterministic order.
    - FR-results-strategy-guard: Enforce strategy existence in ResultStore.

Python API Usage:
    from app.workspace.results.app_results import AppResultsService
    service = AppResultsService()
    res = service.get_data_items("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results data-items --project-id proj_1 \
        --databank Results --strategy-id Strat_01
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore

logger = get_logger(__name__)


def wrap_response[T](
    request_id: str,
    data: T,
    json_payload: Any,
    revision: int | None = None,
) -> StandardResponse[T]:
    """Validate json_payload through StandardResponse and attach typed data.

    Args:
        request_id: Operation request identifier.
        data: Typed domain entity payload.
        json_payload: JSON-serializable representation for validation.
        revision: Optional version counter.

    Returns:
        StandardResponse envelope enclosing typed data entity.
    """
    envelope: StandardResponse[Any] = StandardResponse(
        request_id=request_id,
        data=json_payload,
        revision=revision,
    )
    object.__setattr__(envelope, "data", data)
    return cast("StandardResponse[T]", envelope)


def to_float(val: object, default: float = 0.0) -> float:
    """Safely convert arbitrary object to float."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            pass
    return default


def to_int(val: object, default: int = 0) -> int:
    """Safely convert arbitrary object to int."""
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    if isinstance(val, str):
        try:
            return int(val)
        except ValueError:
            pass
    return default


@dataclass(frozen=True, slots=True)
class AppResultsDataItem:
    """Represents a single selectable result key/market for a strategy."""

    result_key: str
    label: str
    symbol: str
    timeframe: str
    sample_type: str
    direction: str
    is_portfolio: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert item to dictionary representation."""
        return {
            "result_key": self.result_key,
            "label": self.label,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "sample_type": self.sample_type,
            "direction": self.direction,
            "is_portfolio": self.is_portfolio,
        }


@dataclass(frozen=True, slots=True)
class AppResultsSelectionState:
    """Active strategy selection state and projection items."""

    project_id: str
    databank_name: str
    strategy_id: str
    active_result_key: str
    active_tab_id: str
    data_items: tuple[AppResultsDataItem, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert selection state to dictionary representation."""
        return {
            "project_id": self.project_id,
            "databank_name": self.databank_name,
            "strategy_id": self.strategy_id,
            "active_result_key": self.active_result_key,
            "active_tab_id": self.active_tab_id,
            "data_items": [item.to_dict() for item in self.data_items],
        }


class AppResultsService:
    """Top-level Results workspace service."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize AppResultsService with optional ResultStore.

        Args:
            store: Backtest result persistence store.
        """
        self.store = store or ResultStore(HostPersistence())
        self._mock_cache: dict[str, RunResult] = {}

    def register_in_memory_result(self, databank_name: str, result: RunResult) -> None:
        """Register an in-memory test or preview result candidate.

        Args:
            databank_name: Name of target databank.
            result: Backtest result record.
        """
        cache_key = f"{databank_name}:{result.strategy_id}"
        self._mock_cache[cache_key] = result
        logger.info(
            "FR-results-selection-state: cached in-memory result key=%s",
            cache_key,
        )

    def _lookup_result(self, databank_name: str, strategy_id: str) -> RunResult | None:
        """Find RunResult from cache or store."""
        cache_key = f"{databank_name}:{strategy_id}"
        run_res = self._mock_cache.get(cache_key)
        if run_res is not None:
            return run_res

        try:
            return self.store.get_result(strategy_id)
        except DomainError:
            summaries = self.store.list_results(databank_name)
            match = next((s for s in summaries if s.strategy_id == strategy_id), None)
            if match is not None:
                return self.store.get_result(match.result_id)
        return None

    def _extract_items(self, run_res: RunResult) -> tuple[AppResultsDataItem, ...]:
        """Extract and order AppResultsDataItems from RunResult."""
        payload = run_res.strategy_payload
        sym = str(payload.get("symbol", run_res.metrics.get("symbol", "EURUSD")))
        tf = str(payload.get("timeframe", run_res.metrics.get("timeframe", "H1")))
        items_map: dict[str, AppResultsDataItem] = {}

        raw_items = payload.get("data_items")
        if isinstance(raw_items, (list, tuple)):
            for raw in raw_items:
                if isinstance(raw, dict):
                    r_key = str(raw.get("result_key", "Main"))
                    items_map[r_key] = AppResultsDataItem(
                        result_key=r_key,
                        label=str(raw.get("label", r_key)),
                        symbol=str(raw.get("symbol", sym)),
                        timeframe=str(raw.get("timeframe", tf)),
                        sample_type=str(raw.get("sample_type", "FullSample")),
                        direction=str(raw.get("direction", "Both")),
                        is_portfolio=bool(raw.get("is_portfolio", False)),
                    )

        if "Main" not in items_map:
            items_map["Main"] = AppResultsDataItem(
                result_key="Main",
                label="Main",
                symbol=sym,
                timeframe=tf,
                sample_type="FullSample",
                direction="Both",
                is_portfolio=False,
            )

        sub_results = payload.get("sub_results")
        if isinstance(sub_results, dict):
            for sub_key, sub_val in sub_results.items():
                if sub_key not in items_map and isinstance(sub_val, dict):
                    items_map[sub_key] = AppResultsDataItem(
                        result_key=sub_key,
                        label=str(sub_val.get("label", sub_key)),
                        symbol=str(sub_val.get("symbol", sym)),
                        timeframe=str(sub_val.get("timeframe", tf)),
                        sample_type=str(sub_val.get("sample_type", "FullSample")),
                        direction=str(sub_val.get("direction", "Both")),
                        is_portfolio=sub_key == "Portfolio",
                    )

        sorted_keys = ["Main"]
        if "Portfolio" in items_map and "Portfolio" not in sorted_keys:
            sorted_keys.append("Portfolio")
        remaining = sorted(k for k in items_map if k not in ("Main", "Portfolio"))
        sorted_keys.extend(remaining)
        return tuple(items_map[k] for k in sorted_keys)

    def get_data_items(
        self, project_id: str, databank_name: str, strategy_id: str
    ) -> StandardResponse[AppResultsSelectionState]:
        """Query strategy stored result bundles and project selection state.

        Args:
            project_id: Project identifier.
            databank_name: Databank container name.
            strategy_id: Strategy identifier.

        Returns:
            StandardResponse containing AppResultsSelectionState.

        Raises:
            DomainError(code='RESULTS_STRATEGY_NOT_FOUND'): When strategy is missing.
        """
        run_res = self._lookup_result(databank_name, strategy_id)
        if run_res is None:
            logger.warning(
                "FR-results-strategy-guard: missing strategy %s in %s (project=%s)",
                strategy_id,
                databank_name,
                project_id,
            )
            raise DomainError(
                code="RESULTS_STRATEGY_NOT_FOUND",
                message=(
                    f"Strategy '{strategy_id}' not found in databank '{databank_name}'"
                ),
                details={
                    "project_id": project_id,
                    "databank_name": databank_name,
                    "strategy_id": strategy_id,
                },
            )

        ordered_items = self._extract_items(run_res)
        state = AppResultsSelectionState(
            project_id=project_id,
            databank_name=databank_name,
            strategy_id=strategy_id,
            active_result_key="Main",
            active_tab_id="overview",
            data_items=ordered_items,
        )

        logger.info(
            "FR-results-selection-state: projected %d items for strategy=%s",
            len(ordered_items),
            strategy_id,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_data_items",
            data=state,
            json_payload=state.to_dict(),
        )
