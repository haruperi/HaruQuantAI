"""Custom Results Plugin host and read-only data bridge service.

Description:
    Implements ResultsPluginsService providing plugin definition CRUD and
    sandboxed read-only strategy data accessors (stats, orders, settings,
    databankStrategies, strategyResultKeys, candles, dataSymbols).

Purpose:
    FEAT-RESULTS-PLUGINS: Custom results plugin host and data bridge.

Key Capabilities:
    - FR-results-plugins-crud: Manage custom results plugin definitions.
    - FR-results-plugins-data: Provide read-only strategy data snapshots.

Python API Usage:
    from app.workspace.results.results_plugins import ResultsPluginsService
    service = ResultsPluginsService()
    plugins = service.list_plugins()

CLI Usage:
    python -m app.cli results plugins list
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import wrap_response

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ResultsPluginDescriptor:
    """Descriptor for a results workspace plugin tab."""

    plugin_id: str
    title: str
    source_html: str
    source_js: str
    is_builtin: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert descriptor to dictionary."""
        return {
            "plugin_id": self.plugin_id,
            "title": self.title,
            "source_html": self.source_html,
            "source_js": self.source_js,
            "is_builtin": self.is_builtin,
        }


class ResultsPluginsService:
    """Custom results plugin host and data bridge service."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}
        self._databank_strategies: dict[str, list[str]] = {}
        self._plugins: dict[str, ResultsPluginDescriptor] = {}
        self._available_symbols: list[str] = ["EURUSD", "GBPUSD", "USDJPY", "SPY"]
        self._init_builtin_plugins()

    def _init_builtin_plugins(self) -> None:
        builtins = (
            ("Overview", "Overview", True),
            ("List of trades", "List of trades", True),
            ("Equity chart", "Equity chart", True),
            ("Trade analysis", "Trade analysis", True),
            ("Source code", "Source code", True),
        )
        for pid, title, is_builtin in builtins:
            self._plugins[pid] = ResultsPluginDescriptor(
                plugin_id=pid,
                title=title,
                source_html="",
                source_js="",
                is_builtin=is_builtin,
            )

    def register_in_memory_result(
        self, result: RunResult, databank_name: str = "Results"
    ) -> None:
        """Register candidate result in memory."""
        self._in_memory_results[result.strategy_id] = result
        self._databank_strategies.setdefault(databank_name, []).append(
            result.strategy_id
        )

    def _resolve_result(self, strategy_id: str) -> RunResult:
        if strategy_id in self._in_memory_results:
            return self._in_memory_results[strategy_id]
        if self.store is not None:
            try:
                return self.store.get_result(strategy_id)
            except DomainError:
                pass
        raise DomainError(
            code="RESULTS_STRATEGY_NOT_FOUND",
            message=f"Strategy '{strategy_id}' not found",
            details={"strategy_id": strategy_id},
        )

    # --- Plugin Definition CRUD ---

    def list_plugins(self) -> StandardResponse[tuple[ResultsPluginDescriptor, ...]]:
        """List all registered results plugins."""
        plugins_tuple = tuple(self._plugins.values())
        return wrap_response(
            request_id="req_list_plugins",
            data=plugins_tuple,
            json_payload={"plugins": [p.to_dict() for p in plugins_tuple]},
        )

    def create_plugin(
        self,
        plugin_id: str,
        title: str,
        source_html: str = "",
        source_js: str = "",
    ) -> StandardResponse[ResultsPluginDescriptor]:
        """Create a new custom results plugin."""
        if plugin_id in self._plugins:
            raise DomainError(
                code="RESULTS_PLUGIN_EXISTS",
                message=f"Plugin '{plugin_id}' already exists",
                details={"plugin_id": plugin_id},
            )
        desc = ResultsPluginDescriptor(
            plugin_id=plugin_id,
            title=title,
            source_html=source_html,
            source_js=source_js,
            is_builtin=False,
        )
        self._plugins[plugin_id] = desc
        logger.info("FR-results-plugins-crud: created plugin %s", plugin_id)
        return wrap_response(
            request_id=f"req_create_plugin_{plugin_id}",
            data=desc,
            json_payload=desc.to_dict(),
        )

    def rename_plugin(
        self, plugin_id: str, new_title: str
    ) -> StandardResponse[ResultsPluginDescriptor]:
        """Rename an existing custom results plugin."""
        if plugin_id not in self._plugins:
            raise DomainError(
                code="RESULTS_PLUGIN_NOT_FOUND",
                message=f"Plugin '{plugin_id}' not found",
                details={"plugin_id": plugin_id},
            )
        old = self._plugins[plugin_id]
        if old.is_builtin:
            raise DomainError(
                code="RESULTS_BUILTIN_PLUGIN_IMMUTABLE",
                message=f"Built-in plugin '{plugin_id}' cannot be renamed",
                details={"plugin_id": plugin_id},
            )
        updated = ResultsPluginDescriptor(
            plugin_id=plugin_id,
            title=new_title,
            source_html=old.source_html,
            source_js=old.source_js,
            is_builtin=False,
        )
        self._plugins[plugin_id] = updated
        logger.info(
            "FR-results-plugins-crud: renamed plugin %s to '%s'", plugin_id, new_title
        )
        return wrap_response(
            request_id=f"req_rename_plugin_{plugin_id}",
            data=updated,
            json_payload=updated.to_dict(),
        )

    def delete_plugin(self, plugin_id: str) -> StandardResponse[bool]:
        """Delete an existing custom results plugin."""
        if plugin_id not in self._plugins:
            raise DomainError(
                code="RESULTS_PLUGIN_NOT_FOUND",
                message=f"Plugin '{plugin_id}' not found",
                details={"plugin_id": plugin_id},
            )
        if self._plugins[plugin_id].is_builtin:
            raise DomainError(
                code="RESULTS_BUILTIN_PLUGIN_IMMUTABLE",
                message=f"Built-in plugin '{plugin_id}' cannot be deleted",
                details={"plugin_id": plugin_id},
            )
        self._plugins.pop(plugin_id)
        logger.info("FR-results-plugins-crud: deleted plugin %s", plugin_id)
        return wrap_response(
            request_id=f"req_delete_plugin_{plugin_id}",
            data=True,
            json_payload={"deleted": True},
        )

    # --- Read-Only Strategy Data Accessors ---

    def get_stats(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        result_key: str = "Main",
    ) -> dict[str, Any]:
        """Get strategy metrics dictionary snapshot."""
        logger.info(
            "FR-results-plugins-data: get_stats proj=%s db=%s strat=%s key=%s",
            project_id,
            databank_name,
            strategy_id,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        return dict(run_res.metrics)

    def get_orders(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        result_key: str = "Main",
    ) -> list[dict[str, Any]]:
        """Get strategy closed trades / orders snapshot."""
        logger.info(
            "FR-results-plugins-data: get_orders proj=%s db=%s strat=%s key=%s",
            project_id,
            databank_name,
            strategy_id,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        return [dict(t) for t in run_res.trades]

    def get_settings(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        result_key: str = "Main",
    ) -> dict[str, Any]:
        """Get strategy settings and payload snapshot."""
        logger.info(
            "FR-results-plugins-data: get_settings proj=%s db=%s strat=%s key=%s",
            project_id,
            databank_name,
            strategy_id,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        return dict(run_res.strategy_payload)

    def list_databank_strategies(
        self, project_id: str, databank_name: str
    ) -> list[str]:
        """List strategy IDs residing in target databank."""
        logger.info(
            "FR-results-plugins-data: list_strategies proj=%s db=%s",
            project_id,
            databank_name,
        )
        return list(self._databank_strategies.get(databank_name, []))

    def get_strategy_result_keys(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
    ) -> tuple[str, ...]:
        """Get available result keys for strategy."""
        logger.info(
            "FR-results-plugins-data: get_keys proj=%s db=%s strat=%s",
            project_id,
            databank_name,
            strategy_id,
        )
        run_res = self._resolve_result(strategy_id)
        keys = ["Main"]
        has_portfolio = (
            "Portfolio" in run_res.strategy_name
            or "constituent_strategy_ids" in run_res.parameters
        )
        if has_portfolio:
            keys.append("Portfolio")
        return tuple(keys)

    def get_candles(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        symbol: str,
        timeframe: str,
    ) -> list[dict[str, Any]]:
        """Get candle series for strategy symbol/timeframe."""
        logger.info(
            "FR-results-plugins-data: get_candles proj=%s db=%s strat=%s sym=%s tf=%s",
            project_id,
            databank_name,
            strategy_id,
            symbol,
            timeframe,
        )
        run_res = self._resolve_result(strategy_id)
        raw_candles = run_res.strategy_payload.get("candles", [])
        if isinstance(raw_candles, (list, tuple)):
            return [dict(c) for c in raw_candles if isinstance(c, dict)]
        return []

    def list_data_symbols(self) -> list[str]:
        """List available market data symbols."""
        return list(self._available_symbols)
