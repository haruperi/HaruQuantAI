"""Safety boundaries package for the Analytics service.

Includes input validation, standard tool envelopes, workload limit enforcement,
and payload redaction logic.
"""

from __future__ import annotations

from app.services.analytics.boundaries.envelopes import (
    AnalyticsError,
    error_envelope,
    success_envelope,
)
from app.services.analytics.boundaries.limits import (
    AnalyticsLimits,
    WorkloadShape,
    enforce_limits,
)
from app.services.analytics.boundaries.redaction import (
    RedactionPolicy,
    redact,
)
from app.services.analytics.boundaries.request_validation import (
    float64,
    request_id,
    validate_request,
)

__all__ = [
    "AnalyticsError",
    "AnalyticsLimits",
    "RedactionPolicy",
    "WorkloadShape",
    "enforce_limits",
    "error_envelope",
    "float64",
    "redact",
    "request_id",
    "success_envelope",
    "validate_request",
]
