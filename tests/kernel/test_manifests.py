"""Unit tests for strict TOML provider manifest parser.

Traces to: P4-T02, Gate G4
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from app.kernel.errors import ManifestValidationError
from app.kernel.manifests import (
    Cardinality,
    EffectClass,
    LifecyclePolicy,
    OnMissing,
    ReloadPolicy,
    load_manifest,
)
from app.kernel.profiles import RuntimeProfile


def _write_manifest(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "manifest.toml"
    p.write_text(content.strip(), encoding="utf-8")
    return p


def test_valid_stateless_manifest(tmp_path: Path) -> None:
    """Verify happy-path loading of a stateless provider manifest."""
    content = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "app.services.indicators.momentum.rsi_default.plugin:create_provider"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "many"

[[requires]]
capability_id = "data.market_dataset.v1"
supported_majors = [1]
cardinality = "exactly_one"
on_missing = "fail_closed"

[runtime]
profiles = ["research", "simulation", "live"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    manifest_path = _write_manifest(tmp_path, content)
    manifest = load_manifest(manifest_path)

    assert str(manifest.provider_id) == "indicator.rsi.default"
    assert str(manifest.provider_version) == "1.0.0"
    assert (
        manifest.entry_point
        == "app.services.indicators.momentum.rsi_default.plugin:create_provider"
    )
    assert len(manifest.provides) == 1
    assert str(manifest.provides[0].capability_id) == "indicator.rsi.v1"
    assert manifest.provides[0].cardinality == Cardinality.MANY
    assert len(manifest.requires) == 1
    assert str(manifest.requires[0].capability_id) == "data.market_dataset.v1"
    assert manifest.requires[0].supported_majors == (1,)
    assert manifest.requires[0].on_missing == OnMissing.FAIL_CLOSED
    assert RuntimeProfile.RESEARCH in manifest.profiles
    assert manifest.effect_classes == (EffectClass.REVERSIBLE_EPHEMERAL,)
    assert manifest.lifecycle == LifecyclePolicy.PURE
    assert manifest.reload == ReloadPolicy.CONFIG_RESTART
    assert manifest.state_schema_id is None
    assert manifest.purge_requires_authorization is False


def test_valid_stateful_manifest(tmp_path: Path) -> None:
    """Verify happy-path loading of a stateful provider manifest."""
    content = """
[provider]
id = "trading.order_execution.default"
version = "2.1.0"
entry_point = "app.services.trading.order_execution.plugin:create_provider"

[[provides]]
capability_id = "trading.order_execution.v2"
contract_version = "2.1.0"
cardinality = "one_of_several"

[runtime]
profiles = ["live"]
scopes = ["tenant"]
effect_classes = ["durable_compensatable", "irreversible_external"]
lifecycle = "scoped"
reload = "process_restart"

[state]
schema_id = "trading_orders"
schema_version = "2.0.0"
migration_manifest = "schema:trading.orders.v2"
compatible_prior_majors = [1, 2]
downgrade_policy = "reject"
uninstall_retention = "retain"
purge_requires_authorization = true
"""
    manifest_path = _write_manifest(tmp_path, content)
    manifest = load_manifest(manifest_path)

    assert manifest.state_schema_id == "trading_orders"
    assert str(manifest.state_schema_version) == "2.0.0"
    assert manifest.migration_manifest == "schema:trading.orders.v2"
    assert manifest.compatible_state_majors == (1, 2)
    assert manifest.uninstall_retention == "retain"
    assert manifest.purge_requires_authorization is True


def test_unknown_root_key_fails_closed(tmp_path: Path) -> None:
    """Verify unknown root-level table/key raises ManifestValidationError."""
    content = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "mod:factory"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"

[extra_table]
foo = "bar"
"""
    p = _write_manifest(tmp_path, content)
    with pytest.raises(ManifestValidationError, match="unknown key 'extra_table'"):
        load_manifest(p)


def test_unknown_table_key_fails_closed(tmp_path: Path) -> None:
    """Verify unknown table key raises ManifestValidationError."""
    content = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "mod:factory"
unknown_field = 123

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    p = _write_manifest(tmp_path, content)
    with pytest.raises(ManifestValidationError, match="unknown key 'unknown_field'"):
        load_manifest(p)


def test_missing_required_key_fails_closed(tmp_path: Path) -> None:
    """Verify missing mandatory key raises ManifestValidationError."""
    content = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    p = _write_manifest(tmp_path, content)
    with pytest.raises(ManifestValidationError, match="missing key 'entry_point'"):
        load_manifest(p)


def test_duplicate_provided_capability_fails_closed(tmp_path: Path) -> None:
    """Verify duplicate capability in [[provides]] raises ManifestValidationError."""
    content = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "many"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.1.0"
cardinality = "many"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    p = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError,
        match=r"duplicate provided capability indicator\.rsi\.v1",
    ):
        load_manifest(p)


def test_duplicate_required_capability_fails_closed(tmp_path: Path) -> None:
    """Verify duplicate capability in [[requires]] raises ManifestValidationError."""
    content = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "mod:factory"

[[requires]]
capability_id = "data.market.v1"
supported_majors = [1]
cardinality = "exactly_one"

[[requires]]
capability_id = "data.market.v1"
supported_majors = [1, 2]
cardinality = "exactly_one"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    p = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError,
        match=r"duplicate required capability data\.market\.v1",
    ):
        load_manifest(p)


def test_malformed_entry_point_fails_closed(tmp_path: Path) -> None:
    """Verify entry points not matching '<module>:<factory>' fail closed."""
    content = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "invalid_entry_point"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    p = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError, match="entry_point must be '<module>:<factory>'"
    ):
        load_manifest(p)


def test_partial_state_table_fails_closed(tmp_path: Path) -> None:
    """Verify partial [state] table fails closed."""
    content = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "mod:factory"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"

[state]
state_schema_id = "my_state"
"""
    p = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError, match="state fields must be all present or all absent"
    ):
        load_manifest(p)


def test_manifest_loading_does_not_import_entry_point(tmp_path: Path) -> None:
    """Verify loading manifest parses strictly without importing the declared entry point module."""
    sentinel_mod_name = "app.test_sentinel_never_imported_module_xyz"
    content = f"""
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "{sentinel_mod_name}:create_provider"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    p = _write_manifest(tmp_path, content)
    manifest = load_manifest(p)
    assert manifest.entry_point == f"{sentinel_mod_name}:create_provider"
    assert sentinel_mod_name not in sys.modules
