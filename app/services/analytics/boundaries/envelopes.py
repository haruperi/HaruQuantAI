"""Standard success/error envelopes and metadata helpers for Analytics boundaries.

All calculations are stateless pure functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.analytics.contracts import ErrorPayload, ToolEnvelope

if TYPE_CHECKING:
    from app.services.analytics.models import AnalyticsMetadata


@dataclass(frozen=True, slots=True)
class AnalyticsError:
    """Structured error descriptor."""

    code: str
    details: str


def success_envelope(
    data: object,
    metadata: AnalyticsMetadata,
) -> ToolEnvelope:
    """Wrap output data inside a standard success envelope."""
    meta_dict = {
        "tool_name": "analytics_tool",
        "tool_category": "analytics",
        "tool_risk_level": "low",
        "request_id": metadata.request_id,
        "schema_version": metadata.schema_version,
        "analytics_engine_version": metadata.analytics_engine_version,
    }
    return ToolEnvelope(
        schema_version=metadata.schema_version,
        status="success",
        message="Operation completed successfully.",
        data=data,
        metadata=meta_dict,
    )


def error_envelope(
    error: AnalyticsError,
    metadata: AnalyticsMetadata,
) -> ToolEnvelope:
    """Wrap structured error info inside a standard error envelope."""
    meta_dict = {
        "tool_name": "analytics_tool",
        "tool_category": "analytics",
        "tool_risk_level": "low",
        "request_id": metadata.request_id,
        "schema_version": metadata.schema_version,
        "analytics_engine_version": metadata.analytics_engine_version,
    }
    err_payload = ErrorPayload(
        code=error.code,
        message=error.details,
    )
    return ToolEnvelope(
        schema_version=metadata.schema_version,
        status="error",
        message="An error occurred.",
        data=None,
        error=err_payload,
        metadata=meta_dict,
    )
