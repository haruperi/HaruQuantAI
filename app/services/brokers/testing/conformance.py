"""One reusable adapter conformance suite (``feature``).

The application Phase 0 reconciliation requires a single conformance suite
applied uniformly to every enabled HaruQuantAI broker route. This module
exposes one pure function, ``run_adapter_conformance``, that returns a
deterministic verdict mapping for one adapter under test. The suite is
fail-closed: any invariant that cannot be proven is reported as ``FAILED``
with a reason rather than silently passing.

The suite is independent of any specific provider SDK: it operates against the
canonical ``BrokerAdapter`` contract surface and the deterministic
``FakeBrokerAdapter`` so it can be applied to every enabled route without a
live connection.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, cast

from app.utils import canonical_digest

if TYPE_CHECKING:
    from app.services.brokers.contracts.protocols import BrokerAdapter
    from app.services.brokers.contracts.responses import StandardResponse

SCHEMA_ID = "brokers.adapter_conformance.v1"

_INVARIANTS = (
    "contract_version_declared",
    "schema_id_declared",
    "is_connected_local_read",
    "capability_gate_enforced",
    "unsupported_capability_fail_closed",
)


class _ConnectLikeAdapter(Protocol):
    """Minimal adapter shape the conformance suite probes directly."""

    contract_version: str
    schema_id: str

    async def is_connected(self) -> StandardResponse[bool]: ...

    async def supports(self, capability: object) -> StandardResponse[bool]: ...


def _require_text(value: object, name: str) -> str:
    """Validate non-empty text.

    Args:
        value: Candidate value.
        name: Field name for diagnostics.

    Returns:
        Validated text.
    """
    if not isinstance(value, str) or not value.strip():
        return f"{name}_missing"
    return value


def _evaluate_contract_version(adapter: _ConnectLikeAdapter) -> tuple[str, str]:
    """Return the contract-version invariant verdict.

    Args:
        adapter: Adapter under test.

    Returns:
        ``(verdict, reason)`` tuple.
    """
    version = _require_text(
        getattr(adapter, "contract_version", ""), "contract_version"
    )
    if version == "v1":
        return "PASSED", "contract_version=v1"
    return "FAILED", version


def _evaluate_schema_id(adapter: _ConnectLikeAdapter) -> tuple[str, str]:
    """Return the schema-id invariant verdict.

    Args:
        adapter: Adapter under test.

    Returns:
        ``(verdict, reason)`` tuple.
    """
    schema = _require_text(getattr(adapter, "schema_id", ""), "schema_id")
    if schema == "brokers.adapter.v1":
        return "PASSED", "schema_id=brokers.adapter.v1"
    return "FAILED", schema


async def _evaluate_is_connected(
    adapter: _ConnectLikeAdapter,
) -> tuple[str, str]:
    """Return the local connection-read invariant verdict.

    Args:
        adapter: Adapter under test.

    Returns:
        ``(verdict, reason)`` tuple.
    """
    response = await adapter.is_connected()
    # is_connected is a purely local state read; it must always return a
    # success response whose data is a boolean, regardless of provider state.
    if response.status == "success" and isinstance(response.data, bool):
        return "PASSED", f"is_connected={response.data}"
    return "FAILED", f"is_connected_status={response.status}"


async def _evaluate_capability_gate(
    adapter: _ConnectLikeAdapter,
    unsupported_capability: object,
) -> tuple[str, str]:
    """Return the capability-gate invariant verdict.

    Args:
        adapter: Adapter under test.
        unsupported_capability: A capability the adapter declares unsupported.

    Returns:
        ``(verdict, reason)`` tuple.
    """
    supports = await adapter.supports(unsupported_capability)
    if supports.status == "success" and supports.data is False:
        return "PASSED", f"supports({unsupported_capability})=False"
    return "FAILED", f"supports_status={supports.status}"


async def _evaluate_unsupported_call(
    adapter: _ConnectLikeAdapter,
    unsupported_operation: str,
) -> tuple[str, str]:
    """Return the fail-closed unsupported-call invariant verdict.

    Args:
        adapter: Adapter under test.
        unsupported_operation: Operation name declared unsupported.

    Returns:
        ``(verdict, reason)`` tuple.
    """
    method = getattr(adapter, unsupported_operation, None)
    if method is None:
        return "FAILED", f"{unsupported_operation}_missing"
    try:
        result = await method(object())
    except Exception as exc:  # noqa: BLE001
        return "FAILED", f"{unsupported_operation}_raised:{type(exc).__name__}"
    result_error = getattr(result, "error", None)
    status = getattr(result, "status", None)
    if (
        status == "error"
        and getattr(result_error, "code", None) == "BROKER_CAPABILITY_UNSUPPORTED"
    ):
        return "PASSED", f"{unsupported_operation}=BROKER_CAPABILITY_UNSUPPORTED"
    return "FAILED", f"{unsupported_operation}_status={status}"


async def run_adapter_conformance(
    *,
    adapter: BrokerAdapter,
    broker_id: str,
    environment: str,
    unsupported_capability: object,
    unsupported_operation: str,
    evaluated_at: datetime | None = None,
) -> dict[str, object]:
    """Run the uniform adapter conformance suite and return a verdict mapping.

    The suite probes five invariants every enabled route must satisfy: declared
    contract version, declared schema id, local connection-read, capability-gate
    enforcement, and fail-closed unsupported-capability behaviour. The verdict
    is fail-closed: an unproven invariant is ``FAILED`` with a deterministic
    reason and the aggregate verdict is ``FAILED`` unless every invariant passes.

    Args:
        adapter: Adapter under test.
        broker_id: Broker identifier of the route under test.
        environment: Environment of the route under test.
        unsupported_capability: A capability identifier the route declares
            unsupported, used to prove the capability gate.
        unsupported_operation: An operation method name declared unsupported,
            used to prove fail-closed behaviour.
        evaluated_at: Optional aware UTC evaluation instant.

    Returns:
        Adapter conformance verdict mapping.

    Raises:
        ValueError: If ``evaluated_at`` is naive or non-UTC.
    """
    moment = evaluated_at if evaluated_at is not None else datetime.now(UTC)
    if moment.tzinfo is None or moment.utcoffset() != UTC.utcoffset(moment):
        raise ValueError("evaluated_at must be aware UTC")
    probe = cast("_ConnectLikeAdapter", adapter)
    version_verdict, version_reason = _evaluate_contract_version(probe)
    schema_verdict, schema_reason = _evaluate_schema_id(probe)
    connected_verdict, connected_reason = await _evaluate_is_connected(probe)
    gate_verdict, gate_reason = await _evaluate_capability_gate(
        probe, unsupported_capability
    )
    unsupported_verdict, unsupported_reason = await _evaluate_unsupported_call(
        probe, unsupported_operation
    )
    results = {
        "contract_version_declared": (version_verdict, version_reason),
        "schema_id_declared": (schema_verdict, schema_reason),
        "is_connected_local_read": (connected_verdict, connected_reason),
        "capability_gate_enforced": (gate_verdict, gate_reason),
        "unsupported_capability_fail_closed": (unsupported_verdict, unsupported_reason),
    }
    verdicts = {name: verdict for name, (verdict, _) in results.items()}
    aggregate = "PASSED" if all(v == "PASSED" for v in verdicts.values()) else "FAILED"
    mapping: dict[str, object] = {
        "schema_id": SCHEMA_ID,
        "broker": _require_text(broker_id, "broker"),
        "environment": _require_text(environment, "environment"),
        "evaluated_at": moment.isoformat().replace("+00:00", "Z"),
        "aggregate_verdict": aggregate,
        "invariants": {
            name: {"verdict": verdict, "reason": reason}
            for name, (verdict, reason) in results.items()
        },
    }
    mapping["integrity_hash"] = canonical_digest(mapping)
    return mapping


__all__ = ["SCHEMA_ID", "run_adapter_conformance"]
