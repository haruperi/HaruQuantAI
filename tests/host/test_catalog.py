"""Unit and integration tests for app.host.catalog: discovery, atomic publication, fingerprints, and admission."""

import hashlib
from pathlib import Path

import pytest
from app.host.catalog import (
    CatalogAdmissionError,
    CatalogRefreshResult,
    CatalogRoot,
    CatalogSnapshot,
    CatalogUnavailableError,
    SelectionRequest,
    SelectionResult,
    _CatalogProvider,
)
from app.plugins.spec import CatalogView, PluginRef

# Probe plugin source template
VALID_PROBE_SOURCE = """
from app.plugins.spec import PluginSpec, PluginRef, OperationSpec, PluginContribution, OperationContribution
from app.plugins.schema import PortSpec, ValueKind

def plugin() -> PluginContribution:
    ref = PluginRef(id="probe.alpha", version=(1, 0, 0))
    op = OperationSpec(
        operation_id="compute",
        title="Probe Alpha",
        inputs=(PortSpec(key="in", kind=ValueKind.NUMBER),),
        outputs=(PortSpec(key="out", kind=ValueKind.NUMBER),),
        effects=("pure",),
    )
    spec = PluginSpec(ref=ref, kind="probe", title="Probe Alpha Plugin", operations=(op,))
    class Impl:
        pass
    return PluginContribution(spec=spec, operations=(OperationContribution("compute", Impl()),))
"""

VALID_PROBE_BETA_SOURCE = """
from app.plugins.spec import PluginSpec, PluginRef, OperationSpec, PluginContribution, OperationContribution
from app.plugins.schema import PortSpec, ValueKind

def plugin() -> PluginContribution:
    ref = PluginRef(id="probe.beta", version=(1, 0, 0))
    op = OperationSpec(
        operation_id="compute",
        title="Probe Beta",
        inputs=(PortSpec(key="in", kind=ValueKind.NUMBER),),
        outputs=(PortSpec(key="out", kind=ValueKind.NUMBER),),
        effects=("pure",),
    )
    spec = PluginSpec(ref=ref, kind="probe", title="Probe Beta Plugin", operations=(op,))
    class Impl:
        pass
    return PluginContribution(spec=spec, operations=(OperationContribution("compute", Impl()),))
"""


def test_empty_catalog_scan_publishes_ready_empty_snapshot(tmp_path: Path) -> None:
    root = CatalogRoot(
        logical_family="probes", path=tmp_path, accepted_kinds=("probe",)
    )
    provider = _CatalogProvider((root,))
    assert not provider.is_ready()

    res = provider.refresh()
    assert res.success is True
    assert provider.is_ready()
    snapshot = provider.snapshot()
    assert snapshot.view.entries == ()
    assert snapshot.whole_fingerprint == hashlib.sha256(b"").hexdigest()


def test_pre_import_candidate_exclusion(tmp_path: Path) -> None:
    # Create valid probe
    (tmp_path / "valid_probe.py").write_text(VALID_PROBE_SOURCE, encoding="utf-8")

    # Files that should be excluded BEFORE import (they would raise if imported)
    (tmp_path / "__init__.py").write_text(
        "raise RuntimeError('Should not import __init__')", encoding="utf-8"
    )
    (tmp_path / "_helper.py").write_text(
        "raise RuntimeError('Should not import underscore')", encoding="utf-8"
    )
    (tmp_path / "test_probe.py").write_text(
        "raise RuntimeError('Should not import test file')", encoding="utf-8"
    )
    (tmp_path / "probe_test.py").write_text(
        "raise RuntimeError('Should not import test file')", encoding="utf-8"
    )
    (tmp_path / "conftest.py").write_text(
        "raise RuntimeError('Should not import conftest')", encoding="utf-8"
    )
    (tmp_path / "notes.txt").write_text("Non-python file", encoding="utf-8")

    root = CatalogRoot(
        logical_family="probes", path=tmp_path, accepted_kinds=("probe",)
    )
    provider = _CatalogProvider((root,))
    res = provider.refresh()

    assert res.success is True
    assert len(provider.snapshot().view.entries) == 1
    assert provider.snapshot().view.entries[0].ref.id == "probe.alpha"


def test_duplicate_plugin_id_rejection_globally(tmp_path: Path) -> None:
    (tmp_path / "probe1.py").write_text(VALID_PROBE_SOURCE, encoding="utf-8")
    (tmp_path / "probe2.py").write_text(VALID_PROBE_SOURCE, encoding="utf-8")

    root = CatalogRoot(
        logical_family="probes", path=tmp_path, accepted_kinds=("probe",)
    )
    provider = _CatalogProvider((root,))
    res = provider.refresh()

    assert res.success is False
    assert not provider.is_ready()
    assert any("Duplicate plugin ID" in issue for issue in res.issues)


def test_initial_failure_and_last_good_refresh_retention(tmp_path: Path) -> None:
    root = CatalogRoot(
        logical_family="probes", path=tmp_path, accepted_kinds=("probe",)
    )
    provider = _CatalogProvider((root,))

    # Step 1: Initial success
    file1 = tmp_path / "alpha.py"
    file1.write_text(VALID_PROBE_SOURCE, encoding="utf-8")
    res1 = provider.refresh()
    assert res1.success is True
    assert len(provider.snapshot().view.entries) == 1
    fp1 = provider.snapshot().whole_fingerprint

    # Step 2: Corrupt candidate added
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("syntax error !!!", encoding="utf-8")
    res2 = provider.refresh()

    # Step 3: Refresh reports failure, but LAST GOOD snapshot is preserved!
    assert res2.success is False
    assert provider.is_ready()
    assert provider.snapshot().whole_fingerprint == fp1
    assert len(provider.snapshot().view.entries) == 1


def test_fingerprints_and_unrelated_stability(tmp_path: Path) -> None:
    root = CatalogRoot(
        logical_family="probes", path=tmp_path, accepted_kinds=("probe",)
    )
    provider = _CatalogProvider((root,))

    file_a = tmp_path / "alpha.py"
    file_a.write_text(VALID_PROBE_SOURCE, encoding="utf-8")
    res1 = provider.refresh()
    assert res1.success is True
    snap1 = provider.snapshot()
    ref_alpha = PluginRef(id="probe.alpha", version=(1, 0, 0))
    alpha_fp1 = snap1.get_entry_fingerprint(ref_alpha)
    whole_fp1 = snap1.whole_fingerprint

    # Add beta
    file_b = tmp_path / "beta.py"
    file_b.write_text(VALID_PROBE_BETA_SOURCE, encoding="utf-8")
    res2 = provider.refresh()
    assert res2.success is True
    snap2 = provider.snapshot()
    ref_beta = PluginRef(id="probe.beta", version=(1, 0, 0))
    assert snap2.view.get_entry(ref_beta) is not None
    alpha_fp2 = snap2.get_entry_fingerprint(ref_alpha)
    whole_fp2 = snap2.whole_fingerprint

    # Unrelated entry fingerprint is unchanged!
    assert alpha_fp1 == alpha_fp2
    # Whole fingerprint changes!
    assert whole_fp1 != whole_fp2


def test_selection_and_default_enabled_empty(tmp_path: Path) -> None:
    (tmp_path / "alpha.py").write_text(VALID_PROBE_SOURCE, encoding="utf-8")
    root = CatalogRoot(
        logical_family="probes", path=tmp_path, accepted_kinds=("probe",)
    )
    provider = _CatalogProvider((root,))
    provider.refresh()

    ref_alpha = PluginRef(id="probe.alpha", version=(1, 0, 0))

    # Request with empty enabled_refs -> operations are NOT_ENABLED
    sel1 = provider.select(SelectionRequest())
    assert sel1.available_operations == ()
    assert len(sel1.unavailable_reasons) == 1
    assert sel1.unavailable_reasons[0] == (ref_alpha, "compute", "NOT_ENABLED")

    # Request with enabled_refs
    sel2 = provider.select(SelectionRequest(enabled_refs=(ref_alpha,)))
    assert sel2.available_operations == ((ref_alpha, "compute"),)
    assert len(sel2.unavailable_reasons) == 0


def test_admission_retention_after_removal(tmp_path: Path) -> None:
    file_a = tmp_path / "alpha.py"
    file_a.write_text(VALID_PROBE_SOURCE, encoding="utf-8")
    root = CatalogRoot(
        logical_family="probes", path=tmp_path, accepted_kinds=("probe",)
    )
    provider = _CatalogProvider((root,))
    provider.refresh()

    ref_alpha = PluginRef(id="probe.alpha", version=(1, 0, 0))
    admitted = provider.admit(ref_alpha, "compute")
    assert admitted.ref == ref_alpha
    assert admitted.operation_id == "compute"
    assert admitted.contribution.implementation is not None

    # Now remove the file from filesystem and refresh catalog
    file_a.unlink()
    res_after = provider.refresh()
    assert res_after.success is True
    assert provider.snapshot().view.entries == ()

    # Previously admitted operation remains completely valid!
    assert admitted.ref == ref_alpha
    assert admitted.contribution.implementation is not None

    # But future admission of the removed plugin fails
    with pytest.raises(CatalogAdmissionError, match="not installed in the catalog"):
        provider.admit(ref_alpha, "compute")


def test_catalog_validations_and_unready_errors(tmp_path: Path) -> None:
    # CatalogRoot validations
    with pytest.raises(TypeError, match=r"must be a pathlib\.Path"):
        CatalogRoot(logical_family="p", path="not-a-path", accepted_kinds=("k",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="accepted_kinds must be a non-empty tuple"):
        CatalogRoot(logical_family="p", path=tmp_path, accepted_kinds=())
    with pytest.raises(ValueError, match="max_files must be > 0"):
        CatalogRoot(
            logical_family="p",
            path=tmp_path,
            accepted_kinds=("k",),
            max_files=0,
        )
    with pytest.raises(ValueError, match="max_source_bytes must be > 0"):
        CatalogRoot(
            logical_family="p",
            path=tmp_path,
            accepted_kinds=("k",),
            max_source_bytes=-1,
        )

    # Unready provider errors
    unready = _CatalogProvider()
    assert unready.is_ready() is False
    with pytest.raises(CatalogUnavailableError, match="Catalog is not ready"):
        unready.snapshot()
    with pytest.raises(CatalogUnavailableError, match="Cannot select"):
        unready.select(SelectionRequest())
    with pytest.raises(CatalogUnavailableError, match="Cannot admit operation"):
        unready.admit(PluginRef(id="p.a", version=(1, 0, 0)), "compute")

    # Snapshot validation
    with pytest.raises(TypeError, match="view must be a CatalogView"):
        CatalogSnapshot(view="not_view", whole_fingerprint="fp")  # type: ignore[arg-type]
    with pytest.raises(
        ValueError, match="whole_fingerprint must be a non-empty string"
    ):
        CatalogSnapshot(view=CatalogView(), whole_fingerprint="")
    with pytest.raises(TypeError, match="entry_fingerprints must be a tuple"):
        CatalogSnapshot(
            view=CatalogView(),
            whole_fingerprint="fp",
            entry_fingerprints="not_tuple",  # type: ignore[arg-type]
        )

    # RefreshResult validation
    with pytest.raises(TypeError, match="success must be a bool"):
        CatalogRefreshResult(success="yes")  # type: ignore[arg-type]

    # SelectionResult validation
    with pytest.raises(TypeError, match="snapshot must be a CatalogSnapshot"):
        SelectionResult(snapshot="not_snap")  # type: ignore[arg-type]
