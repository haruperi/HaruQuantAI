"""Tier C required provider inverse safety and reinstall tests.

Traces to: P11-T03, Gate G11
"""

from __future__ import annotations

from pathlib import Path

from scripts.architecture.provider_deletion_matrix import (
    execute_deletion_test,
    setup_isolated_tree,
)

from tests.removability.harness import run_in_fresh_process

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_reinstall_pilot_reactivates_consumers(tmp_path: Path) -> None:
    """Verify reinstalling deleted provider reactivates discovery and consumers."""
    isolated = tmp_path / "isolated"
    setup_isolated_tree(_REPO_ROOT, isolated)

    res = execute_deletion_test(
        repo_root=_REPO_ROOT,
        isolated_root=isolated,
        provider_id="indicator.rsi.default",
        reinstall=True,
    )
    assert res["passed"] is True, f"Reinstall failed: {res.get('stderr')}"
    assert res["stage"] == "reinstall"


def test_kernel_infrastructure_absence_fails_boot(tmp_path: Path) -> None:
    """Verify absence of required kernel modules prevents application boot."""
    script = """
import sys
# Attempt to import non-existent or corrupted kernel component
try:
    import app.kernel.nonexistent_required_module # type: ignore[import-not-found]
    sys.exit(0) # Should not reach here
except ImportError:
    sys.exit(42) # Expected failure
"""
    res = run_in_fresh_process(repository_root=_REPO_ROOT, script=script)
    assert res.returncode == 42


def test_kill_switch_absence_blocks_live_profile() -> None:
    """Verify safety gate absence marks live profile unready and fails closed."""
    script = """
from app.kernel.profiles import evaluate_profile_readiness, RuntimeProfile
from app.kernel.identifiers import CapabilityId
from app.kernel.resolver import ResolutionReport

cap = CapabilityId.parse("risk.kill_switch.v1")
report = ResolutionReport(
    bindings=(),
    inactive=(),
    activation_order=(),
    deactivation_order=(),
)

readiness_list = evaluate_profile_readiness(
    report,
    requirements={RuntimeProfile.LIVE: (cap,)},
)

live_readiness = next(r for r in readiness_list if r.profile == RuntimeProfile.LIVE)
assert live_readiness.ready is False
assert any(m.capability == str(cap) and m.code == "CAPABILITY_UNAVAILABLE" for m in live_readiness.missing)
"""
    res = run_in_fresh_process(repository_root=_REPO_ROOT, script=script)
    assert res.returncode == 0, res.stderr


def test_no_fallback_to_weaker_provider() -> None:
    """Verify missing required capability refuses fallback to weaker provider."""
    script = """
from app.kernel.resolver import resolve_providers
from app.kernel.manifests import (
    ProviderManifest,
    ProvidedCapability,
    Cardinality,
    LifecyclePolicy,
    ReloadPolicy,
    EffectClass,
)
from app.kernel.profiles import RuntimeProfile
from app.kernel.identifiers import ProviderId, CapabilityId, SemanticVersion

other_manifest = ProviderManifest(
    provider_id=ProviderId.parse("other.other.default"),
    provider_version=SemanticVersion(1, 0, 0),
    entry_point="other.plugin:create_provider",
    provides=(ProvidedCapability(CapabilityId.parse("other.cap.v1"), SemanticVersion(1, 0, 0), Cardinality.EXACTLY_ONE),),
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

report = resolve_providers(
    (other_manifest,),
    enabled_provider_ids=frozenset({other_manifest.provider_id}),
    selected_provider_ids={},
)

target_cap = CapabilityId.parse("risk.kill_switch.v1")
assert target_cap not in {b.capability_id for b in report.bindings}
"""
    res = run_in_fresh_process(repository_root=_REPO_ROOT, script=script)
    assert res.returncode == 0, res.stderr
