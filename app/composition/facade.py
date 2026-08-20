"""Context-bound runtime bridge for backward-compatible domain façades.

Traces to: P9-T05, Gate G9
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from contextvars import ContextVar
from typing import TYPE_CHECKING

from app.kernel.errors import (
    CapabilityReasonCode,
    CapabilityUnavailable,
    CapabilityUnavailableError,
)

if TYPE_CHECKING:
    from app.composition.generations import CapabilityLease
    from app.composition.runtime import CompositionRuntime
    from app.kernel.identifiers import CapabilityId

_ACTIVE_RUNTIME: ContextVar[CompositionRuntime | None] = ContextVar(
    "_ACTIVE_RUNTIME", default=None
)
_FALLBACK_RUNTIME_STACK: list[CompositionRuntime] = []

__all__: tuple[str, ...] = ()


@contextlib.contextmanager
def bind_runtime(runtime: CompositionRuntime) -> Iterator[None]:
    """Bind a CompositionRuntime to the current execution context.

    Args:
        runtime: Active CompositionRuntime instance to bind.

    Yields:
        None.
    """
    token = _ACTIVE_RUNTIME.set(runtime)
    _FALLBACK_RUNTIME_STACK.append(runtime)
    try:
        yield
    finally:
        if _FALLBACK_RUNTIME_STACK:
            _FALLBACK_RUNTIME_STACK.pop()
        _ACTIVE_RUNTIME.reset(token)


def lease_capability(capability_id: CapabilityId) -> CapabilityLease[object]:
    """Acquire a capability lease from the current context-bound runtime.

    Args:
        capability_id: Capability identifier to resolve.

    Returns:
        CapabilityLease[object]: Active capability lease.

    Raises:
        CapabilityUnavailableError: If no runtime is bound or capability is absent.
    """
    runtime = _ACTIVE_RUNTIME.get()
    if runtime is None and _FALLBACK_RUNTIME_STACK:
        runtime = _FALLBACK_RUNTIME_STACK[-1]

    if runtime is None:
        detail = CapabilityUnavailable(
            code="CAPABILITY_UNAVAILABLE",
            reason_code=CapabilityReasonCode.NOT_INSTALLED,
            capability=str(capability_id),
            consumer="compatibility_facade",
            provider_id=None,
            provider_state="NOT_INSTALLED",
            profile=None,
            dependency_chain=("compatibility_facade", str(capability_id)),
            retryable=False,
        )
        raise CapabilityUnavailableError(detail)

    try:
        return runtime.lease(capability_id)
    except CapabilityUnavailableError as exc:
        detail = CapabilityUnavailable(
            code="CAPABILITY_UNAVAILABLE",
            reason_code=exc.detail.reason_code,
            capability=str(capability_id),
            consumer="compatibility_facade",
            provider_id=exc.detail.provider_id,
            provider_state=exc.detail.provider_state,
            profile=exc.detail.profile,
            dependency_chain=("compatibility_facade", str(capability_id)),
            retryable=exc.detail.retryable,
        )
        raise CapabilityUnavailableError(detail) from exc
