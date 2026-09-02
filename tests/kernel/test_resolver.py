"""Unit tests for kernel provider resolver and topological activation ordering."""

from __future__ import annotations

from app.kernel.identifiers import ProviderId
from app.kernel.manifests import (
    ProvidedCapability,
    ProviderManifest,
    RequiredCapability,
)
from app.kernel.resolver import (
    ResolutionReport,
    resolve_providers,
)


def test_resolve_providers_linear_dependency() -> None:
    """Verify resolve_providers produces correct activation order for linear dependencies."""
    # m1 provides data.market.v1
    m1 = ProviderManifest(
        id="data.market.default",
        version="1.0.0",
        provides=(ProvidedCapability(capability_id="data.market.v1"),),
    )

    # m2 requires data.market.v1 and provides indicator.rsi.v1
    m2 = ProviderManifest(
        id="indicator.rsi.default",
        version="1.2.0",
        provides=(ProvidedCapability(capability_id="indicator.rsi.v1"),),
        requires=(RequiredCapability(capability_id="data.market.v1"),),
    )

    report = resolve_providers(
        (m1, m2),
        enabled_provider_ids=frozenset(
            {
                ProviderId.parse("data.market.default"),
                ProviderId.parse("indicator.rsi.default"),
            }
        ),
    )

    assert isinstance(report, ResolutionReport)
    assert len(report.bindings) == 2
    assert len(report.inactive) == 0

    # m1 must activate before m2
    assert report.activation_order == (
        ProviderId.parse("data.market.default"),
        ProviderId.parse("indicator.rsi.default"),
    )
    # deactivation is reverse
    assert report.deactivation_order == (
        ProviderId.parse("indicator.rsi.default"),
        ProviderId.parse("data.market.default"),
    )


def test_resolve_providers_missing_mandatory_dependency_marks_inactive() -> None:
    """Verify manifests with missing mandatory dependencies are marked inactive."""
    # m2 requires data.market.v1, but data provider is not enabled
    m2 = ProviderManifest(
        id="indicator.rsi.default",
        version="1.0.0",
        provides=(ProvidedCapability(capability_id="indicator.rsi.v1"),),
        requires=(RequiredCapability(capability_id="data.market.v1", optional=False),),
    )

    report = resolve_providers(
        (m2,),
        enabled_provider_ids=frozenset({ProviderId.parse("indicator.rsi.default")}),
    )

    assert len(report.bindings) == 0
    assert len(report.activation_order) == 0
    assert len(report.inactive) > 0
    inactive_caps = [str(inact.capability_id) for inact in report.inactive]
    assert "indicator.rsi.v1" in inactive_caps
    assert "data.market.v1" in inactive_caps


def test_resolve_providers_optional_dependency_handled() -> None:
    """Verify optional dependencies do not prevent provider activation if missing."""
    m = ProviderManifest(
        id="analytics.perf.default",
        version="1.0.0",
        provides=(ProvidedCapability(capability_id="analytics.perf.v1"),),
        requires=(RequiredCapability(capability_id="optional.feed.v1", optional=True),),
    )

    report = resolve_providers(
        (m,),
        enabled_provider_ids=frozenset({ProviderId.parse("analytics.perf.default")}),
    )

    assert len(report.bindings) == 1
    assert len(report.inactive) == 0
    assert report.activation_order == (ProviderId.parse("analytics.perf.default"),)
