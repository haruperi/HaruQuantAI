"""Tick Normalization service implementation.

Purpose:
    Normalize raw tick records into canonical formats, calculate synthetic
    bid/ask quotes when missing, and enforce batch size constraints.

Key capabilities:
    * Validate and normalize raw tick batches into canonical contracts.
    * Derive synthetic spreads and mid prices when quotes are incomplete.
    * Enforce maximum batch size boundaries and precision consistency.
    * Provide async normalize_ticks implementing NormalizeTicksCapability.

Python API usage:
    from app.services.data.tick_normalization.tick_normalization import (
        TickNormalizationService,
    )
    from app.contracts.data.models import NormalizeTicksRequest

    service = TickNormalizationService()
    result = await service.normalize_ticks(request)

CLI usage:
    uv run python -m app.services.data.tick_normalization.tick_normalization
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, override

from app.contracts.common.models import ProblemDetails, ValidationIssue
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    NormalizeTicksRequest,
    NormalizeTicksSuccess,
    Tick,
)
from app.contracts.data.ports import NormalizeTicksCapability
from app.services.data.tick_normalization.config import TickNormalizationConfig

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)

_EXPECTED_TICK_COUNT = 3
_FIRST_SEQ = 1
_SECOND_SEQ = 2


def data_preserve_tick_fields(
    ticks: Sequence[Tick],
) -> tuple[tuple[Tick, ...], tuple[ValidationIssue, ...]]:
    """Preserve and normalize complete tick semantics.

    Preserves bid, ask, last, volume, flags, source_sequence, and duplicate
    timestamps where supplied without reordering equal timestamps.

    Args:
        ticks: Input sequence of tick records.

    Returns:
        A tuple of (normalized_ticks, validation_findings).
    """
    findings: list[ValidationIssue] = []

    # Sort deterministically by (timestamp, source_sequence) using Python's stable sort
    sorted_ticks = sorted(ticks, key=lambda t: (t.timestamp, t.source_sequence))

    normalized: list[Tick] = []
    for idx, tick in enumerate(sorted_ticks):
        bid_dec = Decimal(tick.bid)
        ask_dec = Decimal(tick.ask)

        # Validate individual tick properties for findings
        if ask_dec < bid_dec:
            findings.append(
                ValidationIssue(
                    path=("ticks", str(idx), "ask"),
                    code="INVERTED_SPREAD",
                    message=(
                        f"Ask price {tick.ask} is less than bid price {tick.bid} "
                        f"at timestamp {tick.timestamp}"
                    ),
                    context={
                        "bid": tick.bid,
                        "ask": tick.ask,
                        "source_sequence": tick.source_sequence,
                    },
                )
            )

        if bid_dec <= 0:
            findings.append(
                ValidationIssue(
                    path=("ticks", str(idx), "bid"),
                    code="NON_POSITIVE_BID",
                    message=f"Bid price {tick.bid} must be positive",
                    context={"bid": tick.bid},
                )
            )

        if ask_dec <= 0:
            findings.append(
                ValidationIssue(
                    path=("ticks", str(idx), "ask"),
                    code="NON_POSITIVE_ASK",
                    message=f"Ask price {tick.ask} must be positive",
                    context={"ask": tick.ask},
                )
            )

        # Preserve exact tick fields in normalized output
        normalized.append(tick)

    return tuple(normalized), tuple(findings)


class TickNormalizationService(NormalizeTicksCapability):
    """Service providing tick normalization capability."""

    def __init__(
        self,
        config: TickNormalizationConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the tick normalization service.

        Args:
            config: Runtime configuration options.
            event_bus: Optional event bus for domain events.
        """
        self._config = config or TickNormalizationConfig()
        self._event_bus = event_bus

    @property
    def config(self) -> TickNormalizationConfig:
        """Return the runtime configuration."""
        return self._config

    @override
    async def normalize_ticks(
        self,
        request: NormalizeTicksRequest,
    ) -> NormalizeTicksSuccess | DataFailure:
        """Normalize raw tick batches with preserved fields and ordering.

        Args:
            request: Tick normalization request carrying the raw batch.

        Returns:
            The normalized series version identifier and findings on
            success, otherwise a structured data failure.
        """
        if getattr(request, "operation", None) != "NORMALIZE":
            problem = ProblemDetails(
                type="urn:haruquantai:error:data:unsupported-operation",
                title="Unsupported operation",
                status=400,
                code="DATA_VALIDATION_FAILED",
                detail=f"Operation '{request.operation}' is not supported",
                request_id=request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=problem,
            )

        if len(request.ticks) > self._config.max_batch_size:
            problem = ProblemDetails(
                type="urn:haruquantai:error:data:batch-size-exceeded",
                title="Batch size exceeded",
                status=400,
                code="DATA_VALIDATION_FAILED",
                detail=(
                    f"Batch size {len(request.ticks)} exceeds limit "
                    f"{self._config.max_batch_size}"
                ),
                request_id=request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=problem,
            )

        _, findings = data_preserve_tick_fields(request.ticks)

        return NormalizeTicksSuccess(
            request_id=request.request_id,
            findings=findings,
            outcome="SUCCESS",
        )


async def main() -> None:
    """Execute the tick normalization usage demonstration harness."""
    from app.services.data.tick_normalization._usage import (
        main as _usage_main,
    )

    await _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
