"""Unit tests for kernel ProviderManifest and manifest loader."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.kernel.errors import ManifestValidationError
from app.kernel.identifiers import ProviderId
from app.kernel.manifests import (
    ProviderManifest,
    load_manifest,
)


def test_provider_manifest_post_init_normalization() -> None:
    """Verify ProviderManifest post-init normalizes id/provider_id and version aliases."""
    m1 = ProviderManifest(provider_id="provider.test.default", version="2.0.0")
    assert m1.id == "provider.test.default"
    assert m1.provider_id == "provider.test.default"
    assert m1.version == "2.0.0"
    assert m1.provider_version == "2.0.0"

    m2 = ProviderManifest(id="provider.other.default", version="3.0.0")
    assert m2.id == "provider.other.default"
    assert m2.provider_id == "provider.other.default"
    assert m2.version == "3.0.0"
    assert m2.provider_version == "3.0.0"


def test_load_manifest_valid_toml(tmp_path: Path) -> None:
    """Verify loading a complete valid manifest TOML file."""
    manifest_file = tmp_path / "manifest.toml"
    manifest_file.write_text(
        """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "pkg.rsi:create_provider"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "exactly_one"

[[requires]]
capability_id = "data.market.v1"
contract_version = "1.0.0"
optional = true

[runtime]
profiles = ["research", "simulation"]
scopes = ["ephemeral"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "singleton"
reload = "dynamic"

[state]
schema_id = "state.rsi.v1"
schema_version = "1.0.0"
migration_manifest = "migrations.toml"
compatible_prior_majors = [1, 2]
downgrade_policy = "deny"
uninstall_retention = "purge"
purge_requires_authorization = true
""",
        encoding="utf-8",
    )

    manifest = load_manifest(manifest_file)
    assert manifest.id == ProviderId.parse("indicator.rsi.default")
    assert manifest.version == "1.0.0"
    assert manifest.entry_point == "pkg.rsi:create_provider"
    assert len(manifest.provides) == 1
    assert str(manifest.provides[0].capability_id) == "indicator.rsi.v1"
    assert len(manifest.requires) == 1
    assert str(manifest.requires[0].capability_id) == "data.market.v1"
    assert manifest.requires[0].optional is True
    assert manifest.profiles == ("research", "simulation")
    assert manifest.scopes == ("ephemeral",)
    assert manifest.effect_classes == ("reversible_ephemeral",)
    assert manifest.lifecycle == "singleton"
    assert manifest.reload == "dynamic"
    assert manifest.state_schema_id == "state.rsi.v1"
    assert manifest.compatible_prior_majors == (1, 2)
    assert manifest.purge_requires_authorization is True


def test_load_manifest_missing_provider_section(tmp_path: Path) -> None:
    """Verify load_manifest raises error when [provider] is missing."""
    manifest_file = tmp_path / "manifest.toml"
    manifest_file.write_text("[other]\nfoo = 'bar'", encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="missing key 'provider'"):
        load_manifest(manifest_file)


def test_load_manifest_invalid_toml_syntax(tmp_path: Path) -> None:
    """Verify load_manifest raises error when file has invalid TOML syntax."""
    manifest_file = tmp_path / "manifest.toml"
    manifest_file.write_text("not = [valid", encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="invalid provider manifest"):
        load_manifest(manifest_file)


def test_load_manifest_invalid_compatible_prior_majors(tmp_path: Path) -> None:
    """Verify load_manifest raises error when compatible_prior_majors contains non-positive numbers."""
    manifest_file = tmp_path / "manifest.toml"
    manifest_file.write_text(
        """
[provider]
id = "indicator.test.default"
version = "1.0.0"
entry_point = "pkg:create"

[state]
compatible_prior_majors = [0, -1]
""",
        encoding="utf-8",
    )

    with pytest.raises(
        ManifestValidationError,
        match="compatible_prior_majors must contain positive integers",
    ):
        load_manifest(manifest_file)
