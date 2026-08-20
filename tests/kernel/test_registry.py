"""Unit tests for provider inventory builder and indexing.

Traces to: P4-T04, Gate G4
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.kernel.discovery import DiscoveredProvider
from app.kernel.errors import ResolutionError
from app.kernel.identifiers import CapabilityId, ProviderId
from app.kernel.manifests import load_manifest
from app.kernel.registry import build_inventory

_MANIFEST_RSI_1 = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""

_MANIFEST_RSI_2 = """
[provider]
id = "indicator.rsi.fast"
version = "1.1.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""

_MANIFEST_WILLIAMS = """
[provider]
id = "indicator.williams_r.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "indicator.williams_r.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""


def test_build_inventory_empty() -> None:
    """Verify empty discovered providers produces empty immutable inventory."""
    inv = build_inventory(())
    assert inv.providers == ()
    assert len(inv.by_provider) == 0
    assert len(inv.by_capability) == 0


def test_build_inventory_sorted_indexes(tmp_path: Path) -> None:
    """Verify inventory indexes providers and capabilities in deterministic sorted order."""
    p_williams = tmp_path / "w.toml"
    p_williams.write_text(_MANIFEST_WILLIAMS.strip(), encoding="utf-8")
    m_williams = load_manifest(p_williams)

    p_rsi = tmp_path / "r.toml"
    p_rsi.write_text(_MANIFEST_RSI_1.strip(), encoding="utf-8")
    m_rsi = load_manifest(p_rsi)

    d1 = DiscoveredProvider(manifest_path=p_williams, manifest=m_williams)
    d2 = DiscoveredProvider(manifest_path=p_rsi, manifest=m_rsi)

    inv = build_inventory((d1, d2))
    assert len(inv.providers) == 2
    assert str(inv.providers[0].provider_id) == "indicator.rsi.default"
    assert str(inv.providers[1].provider_id) == "indicator.williams_r.default"


def test_build_inventory_immutable_maps(tmp_path: Path) -> None:
    """Verify inventory mapping proxy cannot be mutated."""
    p_rsi = tmp_path / "r.toml"
    p_rsi.write_text(_MANIFEST_RSI_1.strip(), encoding="utf-8")
    m_rsi = load_manifest(p_rsi)
    d = DiscoveredProvider(manifest_path=p_rsi, manifest=m_rsi)

    inv = build_inventory((d,))
    with pytest.raises(TypeError):
        inv.by_provider[ProviderId.parse("indicator.rsi.default")] = m_rsi  # type: ignore[index]

    with pytest.raises(TypeError):
        inv.by_capability[CapabilityId.parse("indicator.rsi.v1")] = ()  # type: ignore[index]


def test_build_inventory_duplicate_rejection(tmp_path: Path) -> None:
    """Verify duplicate provider IDs raise ResolutionError."""
    p_rsi = tmp_path / "r.toml"
    p_rsi.write_text(_MANIFEST_RSI_1.strip(), encoding="utf-8")
    m_rsi = load_manifest(p_rsi)
    d1 = DiscoveredProvider(manifest_path=p_rsi, manifest=m_rsi)
    d2 = DiscoveredProvider(manifest_path=p_rsi, manifest=m_rsi)

    with pytest.raises(
        ResolutionError,
        match=r"duplicate provider id: indicator\.rsi\.default",
    ):
        build_inventory((d1, d2))


def test_build_inventory_multiple_providers_per_capability(tmp_path: Path) -> None:
    """Verify multiple providers providing the same capability are indexed together."""
    p1 = tmp_path / "r1.toml"
    p1.write_text(_MANIFEST_RSI_1.strip(), encoding="utf-8")
    m1 = load_manifest(p1)

    p2 = tmp_path / "r2.toml"
    p2.write_text(_MANIFEST_RSI_2.strip(), encoding="utf-8")
    m2 = load_manifest(p2)

    inv = build_inventory(
        (
            DiscoveredProvider(manifest_path=p1, manifest=m1),
            DiscoveredProvider(manifest_path=p2, manifest=m2),
        )
    )

    cap_id = CapabilityId.parse("indicator.rsi.v1")
    assert cap_id in inv.by_capability
    provs = inv.by_capability[cap_id]
    assert len(provs) == 2
    assert [str(p.provider_id) for p in provs] == [
        "indicator.rsi.default",
        "indicator.rsi.fast",
    ]
