"""Unit tests for CompositionRuntime and capability lifecycle management."""

from __future__ import annotations

from typing import Any

import pytest
from app.composition.facade import CapabilityLease
from app.composition.runtime import CompositionRuntime
from app.kernel.errors import CapabilityUnavailableError
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.manifests import (
    ProvidedCapability,
    ProviderManifest,
    RequiredCapability,
)
from app.kernel.profiles import CapabilityUnavailable
from app.kernel.resolver import (
    InactiveCapability,
    ResolutionReport,
    ResolvedBinding,
)


def test_composition_runtime_activate_and_lease() -> None:
    """Verify CompositionRuntime activates providers, supplies dependencies, and leases capabilities."""
    runtime = CompositionRuntime()

    cap_data = CapabilityId.parse("data.market.v1")
    cap_indicator = CapabilityId.parse("indicator.rsi.v1")
    prov_data = ProviderId.parse("data.market.default")
    prov_indicator = ProviderId.parse("indicator.rsi.default")

    manifest_data = ProviderManifest(
        id=prov_data,
        version="1.0.0",
        provides=(ProvidedCapability(capability_id=cap_data),),
    )
    manifest_indicator = ProviderManifest(
        id=prov_indicator,
        version="1.0.0",
        provides=(ProvidedCapability(capability_id=cap_indicator),),
        requires=(RequiredCapability(capability_id=cap_data),),
    )

    report = ResolutionReport(
        bindings=(
            ResolvedBinding(
                capability_id=cap_data,
                provider_id=prov_data,
                provider_version=SemanticVersion(1, 0, 0),
            ),
            ResolvedBinding(
                capability_id=cap_indicator,
                provider_id=prov_indicator,
                provider_version=SemanticVersion(1, 0, 0),
            ),
        ),
        inactive=(),
        activation_order=(prov_data, prov_indicator),
        deactivation_order=(prov_indicator, prov_data),
    )

    data_instance = {"name": "data_provider"}
    indicator_instance = {"name": "indicator_provider"}

    def factory_data(
        dependencies: dict[Any, Any], config: dict[str, Any], scope: Any
    ) -> Any:
        return data_instance

    def factory_indicator(
        dependencies: dict[Any, Any], config: dict[str, Any], scope: Any
    ) -> Any:
        assert cap_data in dependencies
        assert dependencies[cap_data] == data_instance
        return indicator_instance

    runtime.activate(
        report,
        factories={
            prov_data: factory_data,
            prov_indicator: factory_indicator,
        },
        configs={
            prov_data: {"opt": 1},
            prov_indicator: {"opt": 2},
        },
        manifests=(manifest_data, manifest_indicator),
    )

    lease1 = runtime.lease(cap_data)
    assert isinstance(lease1, CapabilityLease)
    assert lease1.instance == data_instance

    lease2 = runtime.lease(cap_indicator)
    assert isinstance(lease2, CapabilityLease)
    assert lease2.instance == indicator_instance

    runtime.close()
    assert len(runtime._instances) == 0
    assert len(runtime._providers) == 0


def test_composition_runtime_lease_unavailable_capability() -> None:
    """Verify leasing an unactivated capability raises CapabilityUnavailableError."""
    runtime = CompositionRuntime()

    cap_inactive = CapabilityId.parse("execution.live.v1")
    report = ResolutionReport(
        bindings=(),
        inactive=(
            InactiveCapability(
                capability_id=cap_inactive,
                detail=CapabilityUnavailable(
                    capability=str(cap_inactive),
                    code="CAPABILITY_UNAVAILABLE",
                    reason_code="DISABLED",
                ),
            ),
        ),
        activation_order=(),
        deactivation_order=(),
    )

    runtime.activate(report, factories={}, configs={})

    with pytest.raises(CapabilityUnavailableError):
        runtime.lease(cap_inactive)

    with pytest.raises(CapabilityUnavailableError):
        runtime.lease("nonexistent.cap.v1")

    runtime.close()
