"""Unit tests for provider manifest and dependency integrity enforcer.

Traces to: P16-T02, Gate G16
"""

from __future__ import annotations

from pathlib import Path

from app.kernel.discovery import DiscoveredProvider
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.manifests import (
    Cardinality,
    EffectClass,
    LifecyclePolicy,
    ProvidedCapability,
    ProviderManifest,
    ReloadPolicy,
)
from app.kernel.profiles import RuntimeProfile
from scripts.architecture.enforce_provider_manifests import (
    check_manifests_integrity,
    run_manifest_check,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MATRIX_PATH = (
    _REPO_ROOT
    / "docs"
    / "dev"
    / "plugin-decoupling"
    / "audit"
    / "removability_matrix.json"
)


def _make_dummy_manifest(pid: str, provides_cap: str | None = None) -> ProviderManifest:
    provides = ()
    if provides_cap:
        provides = (
            ProvidedCapability(
                CapabilityId.parse(provides_cap),
                SemanticVersion(1, 0, 0),
                Cardinality.EXACTLY_ONE,
            ),
        )
    return ProviderManifest(
        provider_id=ProviderId.parse(pid),
        provider_version=SemanticVersion(1, 0, 0),
        entry_point="dummy.plugin:create_provider",
        provides=provides,
        requires=(),
        optional_requires=(),
        profiles=(RuntimeProfile.LIVE,),
        scopes=("process",),
        effect_classes=(EffectClass.REVERSIBLE_EPHEMERAL,),
        lifecycle=LifecyclePolicy.SCOPED,
        reload=ReloadPolicy.PROCESS_RESTART,
        config_schema=None,
        state_schema_id=None,
        state_schema_version=None,
        migration_manifest=None,
        compatible_state_majors=(),
        uninstall_retention=None,
        purge_requires_authorization=False,
    )


def test_duplicate_manifest_detected(tmp_path: Path) -> None:
    """Verify duplicate provider IDs trigger violation."""
    m1 = _make_dummy_manifest("test.provider.one")
    disc1 = DiscoveredProvider(tmp_path / "p1" / "manifest.toml", m1)
    disc2 = DiscoveredProvider(tmp_path / "p2" / "manifest.toml", m1)

    violations = check_manifests_integrity([disc1, disc2], {}, tmp_path)
    assert any(v.code == "PROVIDER_MANIFEST_DUPLICATE" for v in violations)


def test_missing_spec_detected(tmp_path: Path) -> None:
    """Verify provided capability without on-disk specification triggers violation."""
    m = _make_dummy_manifest("test.provider.one", "nonexistent.cap.v1")
    disc = DiscoveredProvider(tmp_path / "p1" / "manifest.toml", m)

    violations = check_manifests_integrity([disc], {}, tmp_path)
    assert any(v.code == "CAPABILITY_SPEC_MISSING" for v in violations)


def test_current_manifest_tree_passes() -> None:
    """Verify all discovered manifests in current repository pass integrity checks."""
    violations = run_manifest_check(_REPO_ROOT, _MATRIX_PATH)
    assert not violations, f"Manifest violations: {[v.format() for v in violations]}"
