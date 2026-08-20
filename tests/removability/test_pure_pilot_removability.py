"""Removability tests proving independent deletion of RSI and Williams %R providers.

Traces to: P9-T06, Gate G9
"""

from __future__ import annotations

import shutil
from pathlib import Path

from tests.removability.harness import run_in_fresh_process

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _setup_isolated_app_tree(tmp_path: Path) -> Path:
    """Copy the app/ package to a temporary path without bytecode caches."""
    app_src = _REPO_ROOT / "app"
    app_dst = tmp_path / "app"
    shutil.copytree(
        app_src,
        app_dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return tmp_path


def test_remove_rsi_provider_only(tmp_path: Path) -> None:
    """Verify deleting RSI provider leaves Williams %R fully functional and RSI unavailable."""
    isolated_root = _setup_isolated_app_tree(tmp_path)
    rsi_dir = (
        isolated_root / "app" / "services" / "indicators" / "momentum" / "rsi_default"
    )
    shutil.rmtree(rsi_dir)
    assert not rsi_dir.exists()

    script = """
from app.kernel.manifests import load_manifest
from app.kernel.identifiers import CapabilityId
from app.kernel.resolver import resolve_providers
from app.composition.runtime import CompositionRuntime
from app.services.indicators.momentum.williams_r_default.plugin import create_provider
from app.kernel.errors import CapabilityUnavailableError
from pathlib import Path

# Williams %R provider manifest exists and loads
w_manifest_path = Path("app/services/indicators/momentum/williams_r_default/manifest.toml")
w_manifest = load_manifest(w_manifest_path)
assert str(w_manifest.provider_id) == "indicator.williams_r.default"

# Resolver resolves Williams %R but RSI has no provider
report = resolve_providers(
    (w_manifest,),
    enabled_provider_ids=frozenset({w_manifest.provider_id}),
    selected_provider_ids={},
)
assert len(report.bindings) == 1
assert str(report.bindings[0].capability_id) == "indicator.williams_r.v1"

# Composition runtime activates Williams %R
runtime = CompositionRuntime()
runtime.activate(
    report,
    factories={w_manifest.provider_id: create_provider},
    configs={w_manifest.provider_id: {}},
)

# Williams %R is leasable
w_lease = runtime.lease(CapabilityId.parse("indicator.williams_r.v1"))
assert w_lease.instance is not None

# RSI is unavailable and fails closed
try:
    runtime.lease(CapabilityId.parse("indicator.rsi.v1"))
    raise AssertionError("RSI lease should have failed")
except CapabilityUnavailableError as exc:
    assert exc.detail.capability == "indicator.rsi.v1"
"""
    res = run_in_fresh_process(repository_root=isolated_root, script=script)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"


def test_remove_williams_r_provider_only(tmp_path: Path) -> None:
    """Verify deleting Williams %R provider leaves RSI fully functional and Williams %R unavailable."""
    isolated_root = _setup_isolated_app_tree(tmp_path)
    w_dir = (
        isolated_root
        / "app"
        / "services"
        / "indicators"
        / "momentum"
        / "williams_r_default"
    )
    shutil.rmtree(w_dir)
    assert not w_dir.exists()

    script = """
from app.kernel.manifests import load_manifest
from app.kernel.identifiers import CapabilityId
from app.kernel.resolver import resolve_providers
from app.composition.runtime import CompositionRuntime
from app.services.indicators.momentum.rsi_default.plugin import create_provider
from app.kernel.errors import CapabilityUnavailableError
from pathlib import Path

# RSI provider manifest exists and loads
rsi_manifest_path = Path("app/services/indicators/momentum/rsi_default/manifest.toml")
rsi_manifest = load_manifest(rsi_manifest_path)
assert str(rsi_manifest.provider_id) == "indicator.rsi.default"

# Resolver resolves RSI
report = resolve_providers(
    (rsi_manifest,),
    enabled_provider_ids=frozenset({rsi_manifest.provider_id}),
    selected_provider_ids={},
)
assert len(report.bindings) == 1
assert str(report.bindings[0].capability_id) == "indicator.rsi.v1"

# Composition runtime activates RSI
runtime = CompositionRuntime()
runtime.activate(
    report,
    factories={rsi_manifest.provider_id: create_provider},
    configs={rsi_manifest.provider_id: {}},
)

# RSI is leasable
rsi_lease = runtime.lease(CapabilityId.parse("indicator.rsi.v1"))
assert rsi_lease.instance is not None

# Williams %R is unavailable and fails closed
try:
    runtime.lease(CapabilityId.parse("indicator.williams_r.v1"))
    raise AssertionError("Williams %R lease should have failed")
except CapabilityUnavailableError as exc:
    assert exc.detail.capability == "indicator.williams_r.v1"
"""
    res = run_in_fresh_process(repository_root=isolated_root, script=script)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"


def test_remove_both_pure_providers(tmp_path: Path) -> None:
    """Verify deleting both pure providers leaves the kernel and indicators framework intact."""
    isolated_root = _setup_isolated_app_tree(tmp_path)
    rsi_dir = (
        isolated_root / "app" / "services" / "indicators" / "momentum" / "rsi_default"
    )
    w_dir = (
        isolated_root
        / "app"
        / "services"
        / "indicators"
        / "momentum"
        / "williams_r_default"
    )
    shutil.rmtree(rsi_dir)
    shutil.rmtree(w_dir)
    assert not rsi_dir.exists()
    assert not w_dir.exists()

    script = """
from app.kernel.identifiers import CapabilityId
from app.kernel.resolver import resolve_providers
from app.composition.runtime import CompositionRuntime
from app.kernel.errors import CapabilityUnavailableError

# Resolver with no provider manifests produces empty bindings
report = resolve_providers((), enabled_provider_ids=frozenset(), selected_provider_ids={})
assert len(report.bindings) == 0

# Runtime boots with empty report
runtime = CompositionRuntime()
runtime.activate(report, factories={}, configs={})

# Both capabilities fail closed
for cap_str in ("indicator.rsi.v1", "indicator.williams_r.v1"):
    try:
        runtime.lease(CapabilityId.parse(cap_str))
        raise AssertionError(f"{cap_str} lease should have failed")
    except CapabilityUnavailableError as exc:
        assert exc.detail.capability == cap_str
"""
    res = run_in_fresh_process(repository_root=isolated_root, script=script)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
