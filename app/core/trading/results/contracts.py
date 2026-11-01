"""Contracts and models for backtest databank results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.lib.errors import JSONValue, copy_json


def _parse_dict_list(raw_items: Any) -> tuple[dict[str, JSONValue], ...]:
    """Safely detach and copy a list of dictionaries."""
    if not isinstance(raw_items, list):
        return ()
    result: list[dict[str, JSONValue]] = []
    for item in raw_items:
        if isinstance(item, dict):
            copied = copy_json(item)
            if isinstance(copied, dict):
                result.append(copied)
    return tuple(result)


def _parse_metrics(raw_metrics: Any) -> dict[str, float | int | str]:
    """Parse scalar metric values from raw dict."""
    if not isinstance(raw_metrics, dict):
        return {}
    metrics: dict[str, float | int | str] = {}
    for k, v in raw_metrics.items():
        if isinstance(v, (int, float, str)):
            metrics[str(k)] = v
    return metrics


@dataclass(frozen=True, slots=True)
class ResultSummary:
    """Lightweight summary of a strategy backtest candidate in a databank."""

    result_id: str
    databank_id: str
    strategy_id: str
    strategy_name: str
    net_profit: float = 0.0
    profit_factor: float = 0.0
    drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    trades_count: int = 0
    win_rate: float = 0.0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize result summary to JSON-compatible dictionary."""
        return {
            "result_id": self.result_id,
            "databank_id": self.databank_id,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "net_profit": self.net_profit,
            "profit_factor": self.profit_factor,
            "drawdown": self.drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "trades_count": self.trades_count,
            "win_rate": self.win_rate,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> ResultSummary:
        """Create a ResultSummary from a database record."""
        return cls(
            result_id=str(record.get("id") or record.get("result_id") or ""),
            databank_id=str(record.get("databank_id", "")),
            strategy_id=str(record.get("strategy_id", "")),
            strategy_name=str(record.get("strategy_name", "")),
            net_profit=float(record.get("net_profit", 0.0)),
            profit_factor=float(record.get("profit_factor", 0.0)),
            drawdown=float(record.get("drawdown", 0.0)),
            sharpe_ratio=float(record.get("sharpe_ratio", 0.0)),
            trades_count=int(record.get("trades_count", 0)),
            win_rate=float(record.get("win_rate", 0.0)),
            created_at=str(record.get("created_at", "")),
            updated_at=str(record.get("updated_at", "")),
        )


@dataclass(frozen=True, slots=True)
class RunResult:
    """Full backtest execution result for a strategy candidate."""

    result_id: str
    databank_id: str
    strategy_id: str
    strategy_name: str
    metrics: dict[str, float | int | str] = field(default_factory=dict)
    trades: tuple[dict[str, JSONValue], ...] = ()
    equity_curve: tuple[dict[str, JSONValue], ...] = ()
    mae_mfe: tuple[dict[str, JSONValue], ...] = ()
    parameters: dict[str, JSONValue] = field(default_factory=dict)
    strategy_payload: dict[str, JSONValue] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_summary(self) -> ResultSummary:
        """Derive lightweight summary containing key performance indicators."""
        drawdown_val = float(
            self.metrics.get("drawdown", self.metrics.get("max_drawdown", 0.0))
        )
        return ResultSummary(
            result_id=self.result_id,
            databank_id=self.databank_id,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            net_profit=float(self.metrics.get("net_profit", 0.0)),
            profit_factor=float(self.metrics.get("profit_factor", 0.0)),
            drawdown=drawdown_val,
            sharpe_ratio=float(self.metrics.get("sharpe_ratio", 0.0)),
            trades_count=int(self.metrics.get("trades_count", len(self.trades))),
            win_rate=float(self.metrics.get("win_rate", 0.0)),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize complete backtest result to JSON-compatible dictionary."""
        return {
            "result_id": self.result_id,
            "databank_id": self.databank_id,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "metrics": dict(self.metrics),
            "trades": [copy_json(t) for t in self.trades],
            "equity_curve": [copy_json(e) for e in self.equity_curve],
            "mae_mfe": [copy_json(m) for m in self.mae_mfe],
            "parameters": copy_json(self.parameters),
            "strategy_payload": copy_json(self.strategy_payload),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunResult:
        """Create a RunResult from a serialized dictionary."""
        metrics = _parse_metrics(data.get("metrics"))
        trades = _parse_dict_list(data.get("trades"))
        equity = _parse_dict_list(data.get("equity_curve"))
        mae_mfe = _parse_dict_list(data.get("mae_mfe"))

        params_raw = data.get("parameters", {})
        params = copy_json(params_raw) if isinstance(params_raw, dict) else {}

        payload_raw = data.get("strategy_payload", {})
        payload = copy_json(payload_raw) if isinstance(payload_raw, dict) else {}

        return cls(
            result_id=str(data.get("result_id", "")),
            databank_id=str(data.get("databank_id", "")),
            strategy_id=str(data.get("strategy_id", "")),
            strategy_name=str(data.get("strategy_name", "")),
            metrics=metrics,
            trades=trades,
            equity_curve=equity,
            mae_mfe=mae_mfe,
            parameters=params if isinstance(params, dict) else {},
            strategy_payload=payload if isinstance(payload, dict) else {},
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )
