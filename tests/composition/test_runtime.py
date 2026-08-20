"""Unit tests for composition runtime dependency injection, atomic generational activation, and leases.

Traces to: P6-T02, Gate G6
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from app.composition.runtime import CompositionRuntime
from app.kernel.effects import EffectScope
from app.kernel.errors import CapabilityUnavailableError, LifecycleError
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.resolver import ResolutionReport, ResolvedBinding

if TYPE_CHECKING:
    from collections.abc import Mapping


def test_runtime_activates_in_dependency_order() -> None:
    """Verify runtime activates providers in declared topological order."""
    p_data = ProviderId.parse("data.market.default")
    p_rsi = ProviderId.parse("indicator.rsi.default")
    c_data = CapabilityId.parse("data.market.v1")
    c_rsi = CapabilityId.parse("indicator.rsi.v1")

    order: list[ProviderId] = []

    def _factory_data(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> str:
        del dependencies, config, scope
        order.append(p_data)
        return "data_instance"

    def _factory_rsi(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> str:
        del config, scope
        order.append(p_rsi)
        assert dependencies[c_data] == "data_instance"
        return "rsi_instance"

    report = ResolutionReport(
        bindings=(
            ResolvedBinding(
                capability_id=c_data,
                provider_id=p_data,
                provider_version=SemanticVersion.parse("1.0.0"),
            ),
            ResolvedBinding(
                capability_id=c_rsi,
                provider_id=p_rsi,
                provider_version=SemanticVersion.parse("1.0.0"),
            ),
        ),
        inactive=(),
        activation_order=(p_data, p_rsi),
        deactivation_order=(p_rsi, p_data),
    )

    runtime = CompositionRuntime()
    gens = runtime.activate(
        report,
        factories={p_data: _factory_data, p_rsi: _factory_rsi},
        configs={},
    )

    assert order == [p_data, p_rsi]
    assert len(gens) == 2

    # Verify direct leases
    lease_data = runtime.lease(c_data)
    assert lease_data.instance == "data_instance"

    lease_rsi = runtime.lease(c_rsi)
    assert lease_rsi.instance == "rsi_instance"

    runtime.deactivate_all()


def test_runtime_missing_factory_raises_lifecycle_error() -> None:
    """Verify missing provider factory raises LifecycleError before any activation."""
    p_data = ProviderId.parse("data.market.default")
    c_data = CapabilityId.parse("data.market.v1")

    report = ResolutionReport(
        bindings=(
            ResolvedBinding(
                capability_id=c_data,
                provider_id=p_data,
                provider_version=SemanticVersion.parse("1.0.0"),
            ),
        ),
        inactive=(),
        activation_order=(p_data,),
        deactivation_order=(p_data,),
    )

    runtime = CompositionRuntime()
    with pytest.raises(
        LifecycleError, match=r"missing provider factory: data\.market\.default"
    ):
        runtime.activate(report, factories={}, configs={})


def test_runtime_partial_failure_rolls_back_and_leaves_incumbent() -> None:
    """Verify activation failure of candidate unwinds candidate and preserves incumbent."""
    p1 = ProviderId.parse("provider.one.default")
    c1 = CapabilityId.parse("capability.one.v1")

    # 1. Activate incumbent
    incumbent_cleaned = False

    def _incumbent_factory(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> str:
        del dependencies, config

        def _cleanup() -> None:
            nonlocal incumbent_cleaned
            incumbent_cleaned = True

        scope.callback(_cleanup)
        return "incumbent_1"

    report1 = ResolutionReport(
        bindings=(
            ResolvedBinding(
                capability_id=c1,
                provider_id=p1,
                provider_version=SemanticVersion.parse("1.0.0"),
            ),
        ),
        inactive=(),
        activation_order=(p1,),
        deactivation_order=(p1,),
    )

    runtime = CompositionRuntime()
    runtime.activate(report1, factories={p1: _incumbent_factory}, configs={})

    assert runtime.lease(c1).instance == "incumbent_1"
    assert incumbent_cleaned is False

    # 2. Attempt candidate that fails mid-way
    candidate_cleaned = False

    def _candidate_factory(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> str:
        del dependencies, config

        def _cleanup() -> None:
            nonlocal candidate_cleaned
            candidate_cleaned = True

        scope.callback(_cleanup)
        raise RuntimeError("candidate explosion")

    with pytest.raises(LifecycleError):
        runtime.activate(report1, factories={p1: _candidate_factory}, configs={})

    # Candidate was rolled back, incumbent is untouched!
    assert candidate_cleaned is True
    assert incumbent_cleaned is False
    assert runtime.lease(c1).instance == "incumbent_1"

    runtime.deactivate_all()
    assert incumbent_cleaned is True


def test_runtime_lease_missing_capability_raises_unavailable() -> None:
    """Verify leasing an uninstalled capability raises CapabilityUnavailableError."""
    runtime = CompositionRuntime()
    c_unknown = CapabilityId.parse("unknown.capability.v1")

    with pytest.raises(CapabilityUnavailableError) as exc_info:
        runtime.lease(c_unknown)

    assert exc_info.value.detail.capability == "unknown.capability.v1"
    assert exc_info.value.detail.reason_code == "NOT_INSTALLED"


def test_runtime_pin_graph_creates_isolated_snapshot() -> None:
    """Verify pin_graph returns an immutable snapshot that remains valid after runtime deactivation."""
    p_data = ProviderId.parse("data.market.default")
    c_data = CapabilityId.parse("data.market.v1")

    report = ResolutionReport(
        bindings=(
            ResolvedBinding(
                capability_id=c_data,
                provider_id=p_data,
                provider_version=SemanticVersion.parse("1.0.0"),
            ),
        ),
        inactive=(),
        activation_order=(p_data,),
        deactivation_order=(p_data,),
    )

    runtime = CompositionRuntime()
    runtime.activate(
        report,
        factories={p_data: lambda *, dependencies, config, scope: "data_instance"},
        configs={},
    )

    pinned = runtime.pin_graph()
    assert p_data in pinned.generations
    assert c_data in pinned.leases
    assert pinned.leases[c_data].instance == "data_instance"

    runtime.deactivate_all()
    # Pinned snapshot retains values
    assert pinned.leases[c_data].instance == "data_instance"
