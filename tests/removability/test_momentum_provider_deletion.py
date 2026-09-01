"""Removability and transitive deactivation tests for momentum providers.

Traces to: P9-T06, Gate G9
"""

from __future__ import annotations

import shutil
from pathlib import Path

from tests.removability.harness import run_in_fresh_process

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONSUMER_DIR = Path(__file__).resolve().parent / "fixtures" / "rsi_consumer"


def _setup_isolated_app_tree(tmp_path: Path) -> Path:
    """Create a lightweight isolated app tree for testing provider deletion."""
    subdirs = [
        "app/__init__.py",
        "app/runtime.py",
        "app/kernel",
        "app/contracts",
        "app/composition",
        "app/services/__init__.py",
        "app/services/data",
        "app/services/indicators/__init__.py",
        "app/services/indicators/core",
        "app/services/indicators/momentum",
    ]
    for sub in subdirs:
        src = _REPO_ROOT / sub
        dst = tmp_path / sub
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif src.is_dir():
            shutil.copytree(
                src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
            )

    fixtures_dst = tmp_path / "tests" / "removability" / "fixtures" / "rsi_consumer"
    fixtures_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        _CONSUMER_DIR,
        fixtures_dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "removability" / "__init__.py").write_text(
        "", encoding="utf-8"
    )
    (tmp_path / "tests" / "removability" / "fixtures" / "__init__.py").write_text(
        "", encoding="utf-8"
    )
    return tmp_path


def test_delete_williams_provider_leaves_rsi_functional(tmp_path: Path) -> None:
    """Verify deleting Williams %R provider does not deactivate RSI or its consumer."""
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
from pathlib import Path
from app.kernel.manifests import load_manifest
from app.kernel.identifiers import CapabilityId
from app.kernel.resolver import resolve_providers
from app.composition.runtime import CompositionRuntime
from app.services.indicators.momentum.rsi_default.plugin import create_provider as rsi_factory
from tests.removability.fixtures.rsi_consumer.plugin import create_provider as consumer_factory

rsi_m = load_manifest(Path("app/services/indicators/momentum/rsi_default/manifest.toml"))
consumer_m = load_manifest(Path("tests/removability/fixtures/rsi_consumer/manifest.toml"))

report = resolve_providers(
    (rsi_m, consumer_m),
    enabled_provider_ids=frozenset({rsi_m.provider_id, consumer_m.provider_id}),
    selected_provider_ids={},
)

assert len(report.bindings) == 2
assert len(report.inactive) == 0

runtime = CompositionRuntime()
runtime.activate(
    report,
    factories={
        rsi_m.provider_id: rsi_factory,
        consumer_m.provider_id: consumer_factory,
    },
    configs={
        rsi_m.provider_id: {},
        consumer_m.provider_id: {},
    },
    manifests=(rsi_m, consumer_m),
)

consumer_lease = runtime.lease(CapabilityId.parse("test.rsi_consumer.v1"))
assert consumer_lease.instance is not None
"""
    res = run_in_fresh_process(repository_root=isolated_root, script=script)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"


def test_delete_rsi_provider_deactivates_consumer_with_chain(tmp_path: Path) -> None:
    """Verify deleting RSI provider deactivates its transitive consumer."""
    isolated_root = _setup_isolated_app_tree(tmp_path)
    rsi_dir = (
        isolated_root / "app" / "services" / "indicators" / "momentum" / "rsi_default"
    )
    shutil.rmtree(rsi_dir)
    assert not rsi_dir.exists()

    script = """
from pathlib import Path
from app.kernel.identifiers import CapabilityId
from app.kernel.manifests import load_manifest
from app.kernel.resolver import resolve_providers
from app.composition.runtime import CompositionRuntime
from app.kernel.errors import CapabilityUnavailableError

consumer_m = load_manifest(Path("tests/removability/fixtures/rsi_consumer/manifest.toml"))

report = resolve_providers(
    (consumer_m,),
    enabled_provider_ids=frozenset({consumer_m.provider_id}),
    selected_provider_ids={},
)

assert len(report.bindings) == 0
assert any(str(item.capability_id) == "indicator.rsi.v1" for item in report.inactive)

runtime = CompositionRuntime()
runtime.activate(report, factories={}, configs={})

try:
    runtime.lease(CapabilityId.parse("test.rsi_consumer.v1"))
    raise AssertionError("Lease should have failed")
except CapabilityUnavailableError as exc:
    assert exc.detail.capability == "test.rsi_consumer.v1"
"""
    res = run_in_fresh_process(repository_root=isolated_root, script=script)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"


def test_reinstall_rsi_reactivates_consumer(tmp_path: Path) -> None:
    """Verify reinstalling deleted RSI provider reactivates the dependent consumer."""
    isolated_root = _setup_isolated_app_tree(tmp_path)
    rsi_dir = (
        isolated_root / "app" / "services" / "indicators" / "momentum" / "rsi_default"
    )
    # 1. Delete RSI
    shutil.rmtree(rsi_dir)
    assert not rsi_dir.exists()

    # 2. Reinstall RSI from source workspace
    shutil.copytree(
        _REPO_ROOT / "app" / "services" / "indicators" / "momentum" / "rsi_default",
        rsi_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    assert rsi_dir.exists()

    script = """
from pathlib import Path
from app.kernel.manifests import load_manifest
from app.kernel.identifiers import CapabilityId
from app.kernel.resolver import resolve_providers
from app.composition.runtime import CompositionRuntime
from app.services.indicators.momentum.rsi_default.plugin import create_provider as rsi_factory
from tests.removability.fixtures.rsi_consumer.plugin import create_provider as consumer_factory

rsi_m = load_manifest(Path("app/services/indicators/momentum/rsi_default/manifest.toml"))
consumer_m = load_manifest(Path("tests/removability/fixtures/rsi_consumer/manifest.toml"))

report = resolve_providers(
    (rsi_m, consumer_m),
    enabled_provider_ids=frozenset({rsi_m.provider_id, consumer_m.provider_id}),
    selected_provider_ids={},
)

assert len(report.bindings) == 2
assert len(report.inactive) == 0

runtime = CompositionRuntime()
runtime.activate(
    report,
    factories={
        rsi_m.provider_id: rsi_factory,
        consumer_m.provider_id: consumer_factory,
    },
    configs={
        rsi_m.provider_id: {},
        consumer_m.provider_id: {},
    },
    manifests=(rsi_m, consumer_m),
)

consumer_lease = runtime.lease(CapabilityId.parse("test.rsi_consumer.v1"))
assert consumer_lease.instance is not None
"""
    res = run_in_fresh_process(repository_root=isolated_root, script=script)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"


def test_unrelated_indicator_hashes_unchanged() -> None:
    """Verify financial baseline outputs and hashes remain completely unchanged."""
    script = """
from tests.architecture.test_plugin_financial_baseline import (
    test_financial_manifest_is_canonical,
    test_financial_artifacts_match_baseline,
)
test_financial_manifest_is_canonical()
test_financial_artifacts_match_baseline()
"""
    res = run_in_fresh_process(repository_root=_REPO_ROOT, script=script)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
