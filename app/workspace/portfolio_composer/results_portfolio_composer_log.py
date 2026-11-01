"""Portfolio Composer execution log projection service.

Description:
    Projects execution diagnostics, allocation breakdowns, and margin rejection
    records accumulated during chronological shared-capital portfolio simulation.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-log: Project chronological log entries and margin rejection counts.
Python API Usage:
    from app.workspace.portfolio_composer.results_portfolio_composer_log import (
        ResultsPortfolioComposerLogService,
        ComposerLogEntry,
        PortfolioComposerLogPayload,
    )
    resp = ResultsPortfolioComposerLogService.get_log(receipt)
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse

if TYPE_CHECKING:
    from app.workspace.portfolio_composer.portfolio_composer import ComposerRunReceipt

logger = get_logger(__name__)


def _to_json_compatible(value: Any) -> Any:
    """Recursively convert tuples and dataclasses to lists and JSON primitives."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, (list, tuple)):
        return [_to_json_compatible(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _to_json_compatible(v) for k, v in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return _to_json_compatible(asdict(value))
    return str(value)


def _build_typed_response[T](
    *,
    request_id: str,
    data: T,
    json_payload: Any,
    revision: int | None = None,
) -> StandardResponse[T]:
    """Validate json_payload through StandardResponse and attach typed data."""
    envelope: StandardResponse[Any] = StandardResponse(
        request_id=request_id,
        data=_to_json_compatible(json_payload),
        revision=revision,
    )
    object.__setattr__(envelope, "data", data)
    return cast("StandardResponse[T]", envelope)


@dataclass(frozen=True, slots=True)
class ComposerLogEntry:
    """Structured diagnostic or reject log entry from portfolio composition."""

    timestamp_ms: int
    level: Literal["INFO", "WARNING", "REJECTED"]
    strategy_id: str | None
    message: str


@dataclass(frozen=True, slots=True)
class PortfolioComposerLogPayload:
    """Payload containing composition log records and evaluation order statistics."""

    entries: tuple[ComposerLogEntry, ...]
    total_orders_evaluated: int
    rejected_margin_orders: int


class ResultsPortfolioComposerLogService:
    """Service providing execution and margin reject logs."""

    @staticmethod
    def get_log(
        receipt: ComposerRunReceipt,
    ) -> StandardResponse[PortfolioComposerLogPayload]:
        """Extract and format execution logs from a completed composition run receipt.

        Args:
            receipt: Completed ComposerRunReceipt instance.

        Returns:
            StandardResponse containing PortfolioComposerLogPayload.
        """
        logger.info(
            "FR-composer-log: projecting log for run_id=%s (entries=%d, rejected=%d)",
            receipt.run_id,
            len(receipt.log_entries),
            receipt.rejected_margin_orders,
        )

        payload = PortfolioComposerLogPayload(
            entries=receipt.log_entries,
            total_orders_evaluated=receipt.total_orders_evaluated,
            rejected_margin_orders=receipt.rejected_margin_orders,
        )

        return _build_typed_response(
            request_id=f"log-{receipt.run_id}",
            data=payload,
            json_payload=asdict(payload),
        )
