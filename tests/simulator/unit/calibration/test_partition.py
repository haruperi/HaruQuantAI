"""Deterministic partition evidence for FEAT-SIM-17."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.simulator import partition_calibration_evidence

SOURCE = "a" * 64
NOW = datetime(2025, 1, 10, tzinfo=UTC)


def evidence(*, late: bool = False) -> list[dict[str, object]]:
    """Return bounded sanitized spread and execution observations."""
    result: list[dict[str, object]] = []
    for index in range(120):
        economic_at = NOW - timedelta(days=2, minutes=index)
        result.append(
            {
                "evidence_id": f"evidence-{index:03d}",
                "component": "spread" if index % 2 == 0 else "latency",
                "value": Decimal(index % 7 + 1),
                "unit": "points" if index % 2 == 0 else "milliseconds",
                "economic_at": economic_at,
                "available_at": NOW + timedelta(seconds=1)
                if late and index == 0
                else economic_at,
                "ingested_at": NOW + timedelta(seconds=1)
                if late and index == 0
                else economic_at,
                "source_checksum": SOURCE,
                "broker": "mt5",
                "server": "demo-server",
                "account_digest": "b" * 64,
                "environment": "demo",
                "symbol": "EURUSD",
                "regime": "scheduled_event" if index % 5 == 0 else "ordinary",
            }
        )
    return result


def identity(*, environment: str = "demo") -> dict[str, object]:
    """Return complete sanitized artifact identity."""
    return {
        "artifact_id": "calibration-eurusd-v1",
        "broker": "mt5",
        "server": "demo-server" if environment == "demo" else "live-server",
        "account_digest": "b" * 64,
        "environment": environment,
        "symbol": "EURUSD",
        "source_identity": SOURCE,
        "source_available_at": NOW,
        "ingested_at": NOW,
        "calibrated_at": NOW,
    }


def policy() -> dict[str, object]:
    """Return predeclared applicability and conformance policy."""
    return {
        "effective_from": NOW,
        "effective_to": NOW + timedelta(days=30),
        "valid_until": NOW + timedelta(days=30),
        "minimum_samples": 3,
        "minimum_coverage": Decimal("0.95"),
        "observed_coverage": Decimal(1),
        "regime": "scheduled_metadata_only",
        "threshold_metric": "mean_absolute_error",
        "threshold_unit": "points",
        "threshold_test": "mae_lte",
        "threshold_tolerance": Decimal(10),
        "confidence": Decimal("0.95"),
        "economic_error_budget": Decimal(10),
    }


def partitions() -> object:
    """Return one deterministic eligible partition bundle."""
    return partition_calibration_evidence(
        evidence(), evaluation_start=NOW, source_identity=SOURCE
    )


def test_partition_is_order_independent_and_disjoint() -> None:
    """FR-SIM-226: input order cannot change immutable partition hashes."""
    from app.services.simulator.calibration.contracts import _PartitionBundle

    first = partitions()
    second = partition_calibration_evidence(
        tuple(reversed(evidence())), evaluation_start=NOW, source_identity=SOURCE
    )
    assert isinstance(first, _PartitionBundle)
    assert isinstance(second, _PartitionBundle)
    assert first.calibration.checksum == second.calibration.checksum
    groups = [
        {record.evidence_id for record in partition.records}
        for partition in (first.calibration, first.validation, first.certification)
    ]
    assert not groups[0] & groups[1]
    assert not groups[0] & groups[2]
    assert not groups[1] & groups[2]
    assert set.union(*groups) == {item["evidence_id"] for item in evidence()}
