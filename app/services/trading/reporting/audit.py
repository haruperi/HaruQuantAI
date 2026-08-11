"""Causally linked immutable execution-audit evidence."""

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.utils import to_json_safe


class _ExecutionAuditRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.execution_audit.v1"] = "trading.execution_audit.v1"
    audit_id: str
    audit_type: Literal[
        "request",
        "intent",
        "ack",
        "fill",
        "cancellation",
        "replacement",
        "error",
        "reconciliation",
        "correction",
    ]
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None
    source_sequence: int
    evidence: Mapping[str, Any]


def build_execution_audit_record(**values: object) -> dict[str, Any]:
    """Build one validated JSON-safe immutable audit record.

    Args:
        **values: Field values matching _ExecutionAuditRecord schema.

    Returns:
        JSON-safe dictionary representation of the execution audit record.

    Raises:
        TypeError: If serialized payload is not a mapping.
    """
    model = _ExecutionAuditRecord.model_validate(values)
    safe = to_json_safe(model.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("audit transport must be a mapping")
    return safe


def parse_execution_audit_record(value: Mapping[str, object]) -> object:
    """Parse one immutable execution-audit mapping.

    Args:
        value: Mapping payload to validate against schema.

    Returns:
        Validated _ExecutionAuditRecord Pydantic model instance.
    """
    return _ExecutionAuditRecord.model_validate(value)


__all__ = ["build_execution_audit_record", "parse_execution_audit_record"]
