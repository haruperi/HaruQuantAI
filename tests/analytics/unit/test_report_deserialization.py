"""Unit coverage for canonical Analytics report deserialization."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.kernel.identity import generate_id
from app.services.analytics import (
    build_performance_report,
    deserialize_analytics_performance_report,
    serialize_report,
)

from tests.analytics._support import NOW, _configured, _source_with_profit, unwrap


def _report() -> Any:
    """Build one validated report carrying every container type.

    Returns:
        Complete two-trade performance report.
    """
    source = _source_with_profit(Decimal(25))
    first = source["closed_trades"][0]  # type: ignore[index]
    source["closed_trades"] = (  # type: ignore[assignment]
        first,
        {**first, "ticket": "ticket-2", "profit": Decimal(-5)},
    )
    return unwrap(
        build_performance_report(
            source,
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=_configured(),
        )
    )


def _serialized(report: Any) -> str:
    """Serialize one report exactly as the artifact is written.

    Args:
        report: Validated report to serialize.

    Returns:
        Canonical JSON text of the complete report.
    """
    return unwrap(serialize_report(report, format_name="json", config=_configured()))


def test_serialization_round_trip_rebuilds_the_report() -> None:
    """deserialize(serialize(r)) faithfully reconstructs a validated report.

    JSON-safe serialization intentionally stringifies Decimal evidence, so
    direct dataclass equality on Decimal-bearing fields cannot hold; the
    contract is structural identity of every owner-level field together with
    canonical-JSON idempotency (see the second-cycle test).
    """
    report = _report()
    rebuilt = unwrap(deserialize_analytics_performance_report(_serialized(report)))
    assert isinstance(rebuilt.sections, tuple)
    assert rebuilt.schema_id == report.schema_id
    assert rebuilt.report_id == report.report_id
    assert rebuilt.request_id == report.request_id
    assert rebuilt.account_currency == report.account_currency
    assert rebuilt.created_at == report.created_at
    assert rebuilt.lineage == report.lineage
    assert rebuilt.hashes == report.hashes
    assert [s.section_key for s in rebuilt.sections] == [
        s.section_key for s in report.sections
    ]
    assert set(rebuilt.precision_metadata) == set(report.precision_metadata)


def test_round_trip_survives_a_second_cycle() -> None:
    """A rebuilt report serializes to identical canonical JSON."""
    once = _serialized(_report())
    rebuilt = unwrap(deserialize_analytics_performance_report(once))
    twice = unwrap(serialize_report(rebuilt, format_name="json", config=_configured()))
    assert once == twice


def test_malformed_json_fails_closed() -> None:
    """Non-JSON text is rejected through the public fail-closed response."""
    response = deserialize_analytics_performance_report("{not json")
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "ANALYTICS_VALIDATION_FAILED"


def test_wrong_schema_identity_fails_closed() -> None:
    """A JSON object without the report schema identity is rejected."""
    response = deserialize_analytics_performance_report('{"schema_id": "other.v1"}')
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "ANALYTICS_VALIDATION_FAILED"


def test_tampered_section_shape_fails_closed() -> None:
    """Removing a required section field is rejected by reconstruction."""
    document = _serialized(_report()).replace('"criticality"', '"criticality_x"', 1)
    response = deserialize_analytics_performance_report(document)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "ANALYTICS_VALIDATION_FAILED"
