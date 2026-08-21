"""Atomic capability-bundle registration and replacement tests."""

from __future__ import annotations

import pytest

from app.kernel.capability import CapabilityKey
from app.kernel.registry import CapabilityAlreadyBoundError, ServiceRegistry
from app.kernel.scope import FeatureScope, ScopeClosedError

CAP_A = CapabilityKey[object]("test.bundle-a", 1)
CAP_B = CapabilityKey[object]("test.bundle-b", 1)


def test_duplicate_identifier_bundle_is_all_or_nothing() -> None:
    """Internal duplicate identifiers cannot leave a partial publication."""
    registry = ServiceRegistry()
    with pytest.raises(CapabilityAlreadyBoundError, match="duplicate identifiers"):
        registry.register_many(
            [
                (CAP_A, object(), "FEAT-TEST-BUNDLE"),
                (CAP_A, object(), "FEAT-TEST-BUNDLE"),
            ]
        )
    assert not registry.is_available(CAP_A)


@pytest.mark.asyncio
async def test_closed_scope_prevents_bundle_publication() -> None:
    """Scope validation happens before registry mutation."""
    registry = ServiceRegistry()
    scope = FeatureScope("FEAT-TEST-CLOSED")
    await scope.close()
    with pytest.raises(ScopeClosedError):
        registry.register_many(
            [(CAP_A, object(), "FEAT-TEST-CLOSED")],
            scope=scope,
        )
    assert not registry.is_available(CAP_A)


@pytest.mark.asyncio
async def test_failed_replacement_validation_preserves_complete_old_bundle() -> None:
    """A rejected replacement preserves every old provider and generation."""
    registry = ServiceRegistry()
    old_a = object()
    old_b = object()
    first_tokens = registry.register_many(
        [
            (CAP_A, old_a, "FEAT-TEST-BUNDLE"),
            (CAP_B, old_b, "FEAT-TEST-BUNDLE"),
        ]
    )
    closed_scope = FeatureScope("FEAT-TEST-BUNDLE")
    await closed_scope.close()

    with pytest.raises(ScopeClosedError):
        registry.replace_many(
            [
                (CAP_A, object(), "FEAT-TEST-BUNDLE"),
                (CAP_B, object(), "FEAT-TEST-BUNDLE"),
            ],
            scope=closed_scope,
        )
    assert registry.resolve(CAP_A) is old_a
    assert registry.resolve(CAP_B) is old_b
    assert registry.get_binding(CAP_A.identifier).token == first_tokens[0]  # type: ignore[union-attr]
    assert registry.get_binding(CAP_B.identifier).token == first_tokens[1]  # type: ignore[union-attr]
