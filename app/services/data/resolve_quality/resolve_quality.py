"""Explicit quality detection and decisions for ``FEAT-DATA-RESOLVE_QUALITY``.

Detection never mutates source evidence. Findings are deterministic for an immutable
stored version, and resolution is represented by an explicit caller-authored
``DataQualityDecision`` rather than a silent repair.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails, SeriesPointKey
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    Bar,
    DataQualityFinding,
    ResolveQualityRequest,
    ResolveQualitySuccess,
    Tick,
)
from app.kernel.identity import generate_uuid7
from app.services.data.resolve_quality.quality_store import QualityStore

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesStoreCapability


def _failure(request_id: str, detail: str) -> DataFailure:
    """Build a stable missing-version failure."""
    return DataFailure(
        request_id=request_id,
        code="DATA_NOT_FOUND",
        problem=ProblemDetails(
            status=404,
            code="DATA_NOT_FOUND",
            detail=detail,
            request_id=request_id,
        ),
    )


def _finding(
    *,
    data_version_id: str,
    rule_code: str,
    severity: str,
    message_value: object,
    timestamp: str | None = None,
    sequence: int = 0,
) -> DataQualityFinding:
    """Construct one deterministic-shaped quality finding."""
    point = (
        SeriesPointKey(timestamp=timestamp, sequence=sequence)
        if timestamp is not None
        else None
    )
    return DataQualityFinding(
        finding_id=generate_uuid7(),
        data_version_id=data_version_id,
        rule_code=rule_code,
        severity=severity,  # type: ignore[arg-type]
        point=point,
        observed=message_value,  # JSON-safe scalar/object from callers below.
    )


def inspect_ticks(
    data_version_id: str,
    ticks: tuple[Tick, ...],
) -> tuple[DataQualityFinding, ...]:
    """Detect explicit tick ordering/key/quote anomalies.

    Args:
        data_version_id: Immutable source version identity.
        ticks: Stored tick evidence.

    Returns:
        Deterministic finding tuple in observation order.
    """
    findings: list[DataQualityFinding] = []
    previous_key: tuple[str, int] | None = None
    seen: set[tuple[str, int]] = set()
    for tick in ticks:
        key = (tick.timestamp, tick.source_sequence)
        if previous_key is not None and key < previous_key:
            findings.append(
                _finding(
                    data_version_id=data_version_id,
                    rule_code="OUT_OF_ORDER_TICK",
                    severity="ERROR",
                    message_value={"previous": list(previous_key), "current": list(key)},
                    timestamp=tick.timestamp,
                    sequence=tick.source_sequence,
                )
            )
        if key in seen:
            findings.append(
                _finding(
                    data_version_id=data_version_id,
                    rule_code="DUPLICATE_TICK_KEY",
                    severity="WARNING",
                    message_value={"timestamp": tick.timestamp, "sequence": tick.source_sequence},
                    timestamp=tick.timestamp,
                    sequence=tick.source_sequence,
                )
            )
        if Decimal(tick.bid) > Decimal(tick.ask):
            findings.append(
                _finding(
                    data_version_id=data_version_id,
                    rule_code="CROSSED_QUOTE",
                    severity="ERROR",
                    message_value={"bid": tick.bid, "ask": tick.ask},
                    timestamp=tick.timestamp,
                    sequence=tick.source_sequence,
                )
            )
        seen.add(key)
        previous_key = key
    return tuple(findings)


def inspect_bars(
    data_version_id: str,
    bars: tuple[Bar, ...],
) -> tuple[DataQualityFinding, ...]:
    """Detect explicit bar ordering, duplicate, and zero-volume evidence.

    Args:
        data_version_id: Immutable source version identity.
        bars: Stored bar evidence.

    Returns:
        Deterministic finding tuple in observation order.
    """
    findings: list[DataQualityFinding] = []
    previous_key: tuple[str, int] | None = None
    seen: set[tuple[str, int]] = set()
    for bar in bars:
        key = (bar.timestamp, bar.source_sequence)
        if previous_key is not None and key < previous_key:
            findings.append(
                _finding(
                    data_version_id=data_version_id,
                    rule_code="OUT_OF_ORDER_BAR",
                    severity="ERROR",
                    message_value={"previous": list(previous_key), "current": list(key)},
                    timestamp=bar.timestamp,
                    sequence=bar.source_sequence,
                )
            )
        if key in seen:
            findings.append(
                _finding(
                    data_version_id=data_version_id,
                    rule_code="DUPLICATE_BAR_KEY",
                    severity="WARNING",
                    message_value={"timestamp": bar.timestamp, "sequence": bar.source_sequence},
                    timestamp=bar.timestamp,
                    sequence=bar.source_sequence,
                )
            )
        if Decimal(bar.volume) == 0:
            findings.append(
                _finding(
                    data_version_id=data_version_id,
                    rule_code="ZERO_VOLUME_BAR",
                    severity="WARNING",
                    message_value="0",
                    timestamp=bar.timestamp,
                    sequence=bar.source_sequence,
                )
            )
        seen.add(key)
        previous_key = key
    return tuple(findings)


class ResolveQualityService:
    """Capability implementation for quality detection and decisions."""

    def __init__(
        self,
        series_store: DataSeriesStoreCapability,
        quality_store: QualityStore,
    ) -> None:
        """Initialize with declared storage dependencies.

        Args:
            series_store: Immutable Data series-store capability.
            quality_store: Feature-owned findings/decisions adapter.
        """
        self._series_store = series_store
        self._quality_store = quality_store

    async def resolve_quality(
        self,
        request: ResolveQualityRequest,
    ) -> ResolveQualitySuccess | DataFailure:
        """Detect findings or persist one explicit resolution decision.

        Args:
            request: Operation-discriminated quality request.

        Returns:
            Contract-native success or stable not-found failure.
        """
        if request.operation == "RESOLVE":
            assert request.decision is not None
            await self._quality_store.record_decision(request.decision)
            return ResolveQualitySuccess(
                request_id=request.request_id,
                decision=request.decision,
            )

        assert request.data_version_id is not None
        ticks = await self._series_store.read_ticks(request.data_version_id)
        if ticks is not None:
            findings = inspect_ticks(request.data_version_id, ticks)
        else:
            bars = await self._series_store.read_bars(request.data_version_id)
            if bars is None:
                return _failure(request.request_id, "Data version is not available")
            findings = inspect_bars(request.data_version_id, bars)
        await self._quality_store.replace_findings(request.data_version_id, findings)
        return ResolveQualitySuccess(
            request_id=request.request_id,
            findings=findings,
        )


async def _demo() -> None:
    """Demonstrate pure crossed-quote detection."""
    tick = Tick(
        timestamp="2026-01-01T00:00:00.000000Z",
        bid="1.2",
        ask="1.1",
        source_sequence=0,
        flags=0,
    )
    print(
        [
            finding.model_dump(mode="json")
            for finding in inspect_ticks(generate_uuid7(), (tick,))
        ]
    )


if __name__ == "__main__":
    asyncio.run(_demo())
