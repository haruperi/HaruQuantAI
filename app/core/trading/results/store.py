"""Persistence service for strategy candidate backtest databank results."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence, SQLiteValue
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import ResultSummary, RunResult

logger = get_logger(__name__)


class ResultStore:
    """Service managing persistence of candidate backtest results in databanks."""

    def __init__(self, persistence: HostPersistence) -> None:
        """Initialize ResultStore with HostPersistence gateway.

        Args:
            persistence: Central SQLite host persistence gateway.
        """
        self.persistence = persistence
        self.persistence.ensure_databanks_schema()

    def save_result(self, databank_id: str, result: RunResult) -> str:
        """Persist or update a backtest result into a target databank.

        Args:
            databank_id: Identifier of target databank.
            result: RunResult candidate result.

        Returns:
            Saved result_id.
        """
        target_result = (
            replace(result, databank_id=databank_id)
            if result.databank_id != databank_id
            else result
        )

        now_iso = datetime.now(UTC).isoformat()
        created_at = target_result.created_at or now_iso
        updated_at = now_iso

        summary = target_result.to_summary()

        row: dict[str, SQLiteValue] = {
            "id": target_result.result_id,
            "databank_id": databank_id,
            "strategy_id": target_result.strategy_id,
            "strategy_name": target_result.strategy_name,
            "net_profit": summary.net_profit,
            "profit_factor": summary.profit_factor,
            "drawdown": summary.drawdown,
            "sharpe_ratio": summary.sharpe_ratio,
            "trades_count": summary.trades_count,
            "win_rate": summary.win_rate,
            "metrics_json": json.dumps(target_result.metrics),
            "result_json": json.dumps(target_result.to_dict()),
            "created_at": created_at,
            "updated_at": updated_at,
        }

        # Check existence
        existing = self.persistence.read_records(
            "databank_results", filters={"id": target_result.result_id}
        )
        data = existing.get("data")
        records = data.get("records", []) if isinstance(data, dict) else []

        if records:
            self.persistence.update_record(
                "databank_results",
                row,
                filters={"id": target_result.result_id},
            )
            logger.info(
                "Updated result %s in databank %s (strategy=%s, net_profit=%.2f)",
                target_result.result_id,
                databank_id,
                target_result.strategy_name,
                summary.net_profit,
            )
        else:
            self.persistence.create_records("databank_results", row)
            logger.info(
                "Saved new result %s into databank %s (strategy=%s, net_profit=%.2f)",
                target_result.result_id,
                databank_id,
                target_result.strategy_name,
                summary.net_profit,
            )

        return target_result.result_id

    def get_result(self, result_id: str) -> RunResult:
        """Load stored candidate backtest result by ID.

        Args:
            result_id: Unique candidate result ID.

        Returns:
            RunResult with full backtest data.

        Raises:
            DomainError(code='RESULT_NOT_FOUND'): If result does not exist.
            DomainError(code='CORRUPT_RESULT_PAYLOAD'): If stored JSON is invalid.
        """
        response = self.persistence.read_records(
            "databank_results", filters={"id": result_id}
        )
        data = response.get("data")
        records = data.get("records", []) if isinstance(data, dict) else []

        if not records:
            logger.warning("Result %s not found in databank", result_id)
            raise DomainError(
                code="RESULT_NOT_FOUND",
                message="Result not found",
                details={"result_id": result_id},
            )

        row = records[0]
        if not isinstance(row, Mapping):
            raise DomainError(
                code="RESULT_NOT_FOUND",
                message="Result not found",
                details={"result_id": result_id},
            )

        raw_json = str(row.get("result_json") or "{}")
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as err:
            logger.exception("Corrupted result payload for %s", result_id)
            raise DomainError(
                code="CORRUPT_RESULT_PAYLOAD",
                message="Stored result payload is invalid JSON",
                details={"result_id": result_id},
            ) from err

        if not isinstance(payload, dict):
            raise DomainError(
                code="CORRUPT_RESULT_PAYLOAD",
                message="Stored result payload is invalid JSON",
                details={"result_id": result_id},
            )

        return RunResult.from_dict(payload)

    def list_results(
        self, databank_id: str, limit: int = 100, offset: int = 0
    ) -> list[ResultSummary]:
        """List databank candidate summaries with key performance metrics.

        Args:
            databank_id: Databank identifier to query.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of ResultSummary items.
        """
        response = self.persistence.read_records(
            "databank_results",
            filters={"databank_id": databank_id},
            limit=limit,
            offset=offset,
        )
        data = response.get("data")
        records = data.get("records", []) if isinstance(data, dict) else []
        return [
            ResultSummary.from_record(row) for row in records if isinstance(row, dict)
        ]

    def delete_result(self, result_id: str) -> bool:
        """Remove a result from its databank.

        Args:
            result_id: Result identifier to remove.

        Returns:
            True if removed, False if not found.
        """
        response = self.persistence.delete_record(
            "databank_results", filters={"id": result_id}
        )
        if not response.get("success", False):
            logger.warning("Delete requested for non-existent result %s", result_id)
            return False

        data = response.get("data")
        affected = data.get("affected_rows", 0) if isinstance(data, dict) else 0
        success = bool(isinstance(affected, int) and affected > 0)
        if success:
            logger.info("Deleted result %s from databank", result_id)
        return success
