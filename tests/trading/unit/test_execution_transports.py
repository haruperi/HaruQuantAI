"""Unit compatibility evidence for Trading execution transports."""

from app.services.trading import (
    build_economic_execution_event,
    build_execution_audit_record,
    parse_economic_execution_event,
    parse_execution_audit_record,
)


def test_economic_event_v1_round_trip() -> None:
    """Economic execution evidence remains a validated JSON-safe mapping."""
    mapping = build_economic_execution_event(
        event_id="economic-001",
        event_type="fill",
        order_id="order-001",
        position_id="position-001",
        correlation_id="correlation-001",
        causation_id=None,
        payload={"quantity": "1"},
    )
    assert mapping["contract_version"] == "v1"
    assert parse_economic_execution_event(mapping).event_id == "economic-001"


def test_execution_audit_v1_round_trip() -> None:
    """Execution audit evidence retains source sequence and causation."""
    mapping = build_execution_audit_record(
        audit_id="audit-001",
        audit_type="fill",
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        causation_id="cause-001",
        source_sequence=1,
        evidence={"fill_id": "fill-001"},
    )
    assert mapping["schema_id"] == "trading.execution_audit.v1"
    assert parse_execution_audit_record(mapping).source_sequence == 1
