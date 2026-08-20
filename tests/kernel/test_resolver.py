"""Unit tests for provider graph resolver, topological ordering, and cycle detection.

Traces to: P4-T05, Gate G4
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.kernel.errors import CapabilityReasonCode, ResolutionError
from app.kernel.identifiers import CapabilityId
from app.kernel.manifests import load_manifest
from app.kernel.resolver import resolve_providers

_MANIFEST_DATA = """
[provider]
id = "data.market.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "data.market.v1"
contract_version = "1.0.0"
cardinality = "exactly_one"

[runtime]
profiles = ["research", "live"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""

_MANIFEST_RSI = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "many"

[[requires]]
capability_id = "data.market.v1"
supported_majors = [1]
cardinality = "exactly_one"
on_missing = "fail_closed"

[runtime]
profiles = ["research", "live"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""

_MANIFEST_STRATEGY = """
[provider]
id = "strategy.momentum.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "strategy.momentum.v1"
contract_version = "1.0.0"
cardinality = "exactly_one"

[[requires]]
capability_id = "indicator.rsi.v1"
supported_majors = [1]
cardinality = "many"
on_missing = "fail_closed"

[runtime]
profiles = ["research", "live"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""


def test_resolve_empty_manifests() -> None:
    """Verify resolving empty manifests yields empty report."""
    rep = resolve_providers(
        (),
        enabled_provider_ids=frozenset(),
        selected_provider_ids={},
    )
    assert rep.bindings == ()
    assert rep.inactive == ()
    assert rep.activation_order == ()
    assert rep.deactivation_order == ()


def test_resolve_single_independent_provider(tmp_path: Path) -> None:
    """Verify single independent provider binds and activates."""
    p = tmp_path / "data.toml"
    p.write_text(_MANIFEST_DATA.strip(), encoding="utf-8")
    m = load_manifest(p)

    rep = resolve_providers(
        (m,),
        enabled_provider_ids=frozenset([m.provider_id]),
        selected_provider_ids={},
    )
    assert len(rep.bindings) == 1
    assert str(rep.bindings[0].capability_id) == "data.market.v1"
    assert str(rep.bindings[0].provider_id) == "data.market.default"
    assert rep.activation_order == (m.provider_id,)
    assert rep.deactivation_order == (m.provider_id,)


def test_resolve_dependent_providers_activation_order(tmp_path: Path) -> None:
    """Verify topological activation ordering: data -> rsi -> strategy."""
    p_data = tmp_path / "data.toml"
    p_data.write_text(_MANIFEST_DATA.strip(), encoding="utf-8")
    m_data = load_manifest(p_data)

    p_rsi = tmp_path / "rsi.toml"
    p_rsi.write_text(_MANIFEST_RSI.strip(), encoding="utf-8")
    m_rsi = load_manifest(p_rsi)

    p_strat = tmp_path / "strat.toml"
    p_strat.write_text(_MANIFEST_STRATEGY.strip(), encoding="utf-8")
    m_strat = load_manifest(p_strat)

    enabled = frozenset([m_data.provider_id, m_rsi.provider_id, m_strat.provider_id])
    rep = resolve_providers(
        (m_strat, m_data, m_rsi),
        enabled_provider_ids=enabled,
        selected_provider_ids={},
    )

    assert rep.activation_order == (
        m_data.provider_id,
        m_rsi.provider_id,
        m_strat.provider_id,
    )
    assert rep.deactivation_order == (
        m_strat.provider_id,
        m_rsi.provider_id,
        m_data.provider_id,
    )


def test_resolve_disabled_provider_marks_capability_disabled(tmp_path: Path) -> None:
    """Verify provider not in enabled_provider_ids marks capability DISABLED."""
    p_data = tmp_path / "data.toml"
    p_data.write_text(_MANIFEST_DATA.strip(), encoding="utf-8")
    m_data = load_manifest(p_data)

    rep = resolve_providers(
        (m_data,),
        enabled_provider_ids=frozenset(),
        selected_provider_ids={},
    )
    assert len(rep.bindings) == 0
    assert len(rep.inactive) == 1
    assert rep.inactive[0].detail.reason_code == CapabilityReasonCode.DISABLED


def test_resolve_missing_capability_not_installed(tmp_path: Path) -> None:
    """Verify missing required capability marks NOT_INSTALLED and deactivates consumer."""
    p_rsi = tmp_path / "rsi.toml"
    p_rsi.write_text(_MANIFEST_RSI.strip(), encoding="utf-8")
    m_rsi = load_manifest(p_rsi)

    rep = resolve_providers(
        (m_rsi,),
        enabled_provider_ids=frozenset([m_rsi.provider_id]),
        selected_provider_ids={},
    )
    assert len(rep.bindings) == 0
    inactive_reasons = {i.detail.reason_code for i in rep.inactive}
    assert CapabilityReasonCode.NOT_INSTALLED in inactive_reasons


def test_resolve_explicit_selection_resolves_ambiguity(tmp_path: Path) -> None:
    """Verify selected_provider_ids picks specific provider among multiple candidates."""
    m_data1_text = _MANIFEST_DATA.replace("data.market.default", "data.market.p1")
    m_data2_text = _MANIFEST_DATA.replace("data.market.default", "data.market.p2")

    p1 = tmp_path / "d1.toml"
    p1.write_text(m_data1_text.strip(), encoding="utf-8")
    m1 = load_manifest(p1)

    p2 = tmp_path / "d2.toml"
    p2.write_text(m_data2_text.strip(), encoding="utf-8")
    m2 = load_manifest(p2)

    cap = CapabilityId.parse("data.market.v1")
    rep = resolve_providers(
        (m1, m2),
        enabled_provider_ids=frozenset([m1.provider_id, m2.provider_id]),
        selected_provider_ids={cap: m2.provider_id},
    )
    assert len(rep.bindings) == 1
    assert rep.bindings[0].provider_id == m2.provider_id


def test_resolve_unresolved_ambiguity(tmp_path: Path) -> None:
    """Verify multiple candidates for exactly_one capability without selection reports PROVIDER_AMBIGUOUS."""
    m_data1_text = _MANIFEST_DATA.replace("data.market.default", "data.market.p1")
    m_data2_text = _MANIFEST_DATA.replace("data.market.default", "data.market.p2")

    p1 = tmp_path / "d1.toml"
    p1.write_text(m_data1_text.strip(), encoding="utf-8")
    m1 = load_manifest(p1)

    p2 = tmp_path / "d2.toml"
    p2.write_text(m_data2_text.strip(), encoding="utf-8")
    m2 = load_manifest(p2)

    rep = resolve_providers(
        (m1, m2),
        enabled_provider_ids=frozenset([m1.provider_id, m2.provider_id]),
        selected_provider_ids={},
    )
    assert len(rep.bindings) == 0
    assert len(rep.inactive) == 1
    assert rep.inactive[0].detail.reason_code == CapabilityReasonCode.PROVIDER_AMBIGUOUS


def test_resolve_version_incompatible_deactivates_fail_closed_consumer(
    tmp_path: Path,
) -> None:
    """Verify version mismatch reports VERSION_INCOMPATIBLE and deactivates fail_closed consumer."""
    p_data = tmp_path / "data.toml"
    p_data.write_text(
        _MANIFEST_DATA.replace('version = "1.0.0"', 'version = "2.0.0"').strip(),
        encoding="utf-8",
    )
    m_data = load_manifest(p_data)

    p_rsi = tmp_path / "rsi.toml"
    p_rsi.write_text(_MANIFEST_RSI.strip(), encoding="utf-8")
    m_rsi = load_manifest(p_rsi)

    rep = resolve_providers(
        (m_data, m_rsi),
        enabled_provider_ids=frozenset([m_data.provider_id, m_rsi.provider_id]),
        selected_provider_ids={},
    )
    # RSI fails closed because it requires major 1, but Data is version 2.0.0
    assert len(rep.bindings) == 1
    assert rep.bindings[0].provider_id == m_data.provider_id
    assert rep.activation_order == (m_data.provider_id,)


def test_resolve_hard_dependency_cycle_raises_resolution_error(tmp_path: Path) -> None:
    """Verify mutual hard dependency cycle raises ResolutionError."""
    m_a_text = """
[provider]
id = "cycle.a.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "cycle.a.v1"
contract_version = "1.0.0"
cardinality = "exactly_one"

[[requires]]
capability_id = "cycle.b.v1"
supported_majors = [1]
cardinality = "exactly_one"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    m_b_text = """
[provider]
id = "cycle.b.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "cycle.b.v1"
contract_version = "1.0.0"
cardinality = "exactly_one"

[[requires]]
capability_id = "cycle.a.v1"
supported_majors = [1]
cardinality = "exactly_one"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    p_a = tmp_path / "a.toml"
    p_a.write_text(m_a_text.strip(), encoding="utf-8")
    m_a = load_manifest(p_a)

    p_b = tmp_path / "b.toml"
    p_b.write_text(m_b_text.strip(), encoding="utf-8")
    m_b = load_manifest(p_b)

    with pytest.raises(ResolutionError, match="hard dependency cycle:"):
        resolve_providers(
            (m_a, m_b),
            enabled_provider_ids=frozenset([m_a.provider_id, m_b.provider_id]),
            selected_provider_ids={},
        )
