"""Health usage examples for API liveness, readiness, and readiness diagnostics."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import check_clock_drift, get_liveness, get_readiness

_REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
_CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


def _context() -> object:
    """Build a minimal authenticated context for readiness demos."""
    return SimpleNamespace(
        principal_type="USER",
        permissions=("ops:read",),
        request_id=_REQUEST_ID,
        correlation_id=_CORRELATION_ID,
    )


def fr_api_018() -> dict[str, object]:
    """FR-API-018: return coarse process liveness through public boundary."""
    response = get_liveness()
    payload = response.data
    payload_data = payload.model_dump() if payload else {}
    return {
        "liveness_status": payload_data["status"] if payload else None,
        "route": response.metadata.route,
        "has_private_dependency_data": "dependencies" in payload_data,
    }


def fr_api_019() -> dict[str, object]:
    """FR-API-019: return protected readiness and dependency status."""
    response = get_readiness(_context())
    payload = response.data
    return {
        "readiness_status": payload.status if payload else None,
        "drift_seconds": str(payload.clock_drift_seconds) if payload else None,
        "dependency_count": len(payload.dependencies) if payload else 0,
    }


def fr_api_059() -> dict[str, object]:
    """FR-API-059: measure signed local-clock drift in seconds."""
    now = datetime.now(UTC)
    reference = now - timedelta(seconds=1)
    drift = check_clock_drift(reference=reference, tolerance_seconds="2")
    return {
        "clock_drift_seconds": str(drift),
        "drift_nonzero": drift != 0,
    }


def main() -> None:
    """Run the health usage scenarios."""
    print(fr_api_018())
    print(fr_api_019())
    print(fr_api_059())


if __name__ == "__main__":
    main()
