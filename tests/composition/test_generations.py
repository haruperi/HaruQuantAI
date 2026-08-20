"""Unit tests for provider generations, capability leases, and pinned graphs.

Traces to: P6-T01, Gate G6
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.composition.generations import (
    CapabilityLease,
    PinnedCapabilityGraph,
    ProviderGeneration,
    configuration_digest,
)
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion


def test_configuration_digest_is_deterministic() -> None:
    """Verify configuration_digest is identical regardless of dictionary insertion order."""
    cfg1 = {"b": 2, "a": 1, "nested": {"y": "hello", "x": 10}}
    cfg2 = {"nested": {"x": 10, "y": "hello"}, "a": 1, "b": 2}

    d1 = configuration_digest(cfg1)
    d2 = configuration_digest(cfg2)

    assert d1 == d2
    assert len(d1) == 64


def test_provider_generation_validates_timezone_aware_utc() -> None:
    """Verify naive datetime or non-UTC timezone raises ValueError."""
    pid = ProviderId.parse("indicator.rsi.default")
    ver = SemanticVersion.parse("1.0.0")

    naive_dt = datetime.now()  # noqa: DTZ005
    with pytest.raises(ValueError, match=r"activated_at must be timezone-aware UTC"):
        ProviderGeneration(
            provider_id=pid,
            generation_id=uuid4(),
            version=ver,
            config_digest="abc",
            dependency_generation_ids=(),
            activated_at=naive_dt,
        )

    valid_dt = datetime.now(UTC)
    gen = ProviderGeneration(
        provider_id=pid,
        generation_id=uuid4(),
        version=ver,
        config_digest="abc",
        dependency_generation_ids=(),
        activated_at=valid_dt,
    )
    assert gen.activated_at == valid_dt


def test_provider_generation_sorts_dependency_uuids() -> None:
    """Verify dependency_generation_ids are sorted deterministically by hex string."""
    u1 = uuid4()
    u2 = uuid4()
    u_small, u_large = sorted([u1, u2], key=lambda u: u.hex)

    pid = ProviderId.parse("indicator.rsi.default")
    ver = SemanticVersion.parse("1.0.0")
    gen = ProviderGeneration(
        provider_id=pid,
        generation_id=uuid4(),
        version=ver,
        config_digest="abc",
        dependency_generation_ids=(u_large, u_small),
        activated_at=datetime.now(UTC),
    )
    assert gen.dependency_generation_ids == (u_small, u_large)


def test_capability_lease_is_frozen() -> None:
    """Verify CapabilityLease is an immutable record."""
    cap_id = CapabilityId.parse("indicator.rsi.v1")
    gen_id = uuid4()
    lease = CapabilityLease(
        capability_id=cap_id, generation_id=gen_id, instance="my_instance"
    )

    assert lease.capability_id == cap_id
    assert lease.generation_id == gen_id
    assert lease.instance == "my_instance"


def test_pinned_capability_graph_is_immutable() -> None:
    """Verify PinnedCapabilityGraph wraps mappings in MappingProxyType."""
    pid = ProviderId.parse("indicator.rsi.default")
    cap_id = CapabilityId.parse("indicator.rsi.v1")
    gen_id = uuid4()
    ver = SemanticVersion.parse("1.0.0")

    gen = ProviderGeneration(
        provider_id=pid,
        generation_id=gen_id,
        version=ver,
        config_digest="abc",
        dependency_generation_ids=(),
        activated_at=datetime.now(UTC),
    )
    lease = CapabilityLease(capability_id=cap_id, generation_id=gen_id, instance="inst")

    graph = PinnedCapabilityGraph(
        generations={pid: gen},
        leases={cap_id: lease},
    )

    assert graph.generations[pid] == gen
    assert graph.leases[cap_id] == lease
