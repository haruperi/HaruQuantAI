from app.contracts.workspace.build_diagnostics import BenchmarkIdentity, BenchmarkMeasurement, DiagnosticStatus, ProviderDiagnostic
from app.services.workspace.build_diagnostics.build_diagnostics import BuildDiagnosticsService


def test_unknown_and_benchmark_mismatch_stay_explicit() -> None:
    service = BuildDiagnosticsService(2, 4096)
    snap = service.snapshot((ProviderDiagnostic("x@1", None, DiagnosticStatus.UNKNOWN, "NO_EVIDENCE", "token=secret"),))
    assert snap.providers[0].status is DiagnosticStatus.UNKNOWN
    assert "secret" not in snap.providers[0].safe_detail
    identity = BenchmarkIdentity("b", 1, "f", "c", "r", "h", "p", "m")
    target = BenchmarkMeasurement(identity, 1.0, "ms")
    changed = BenchmarkMeasurement(BenchmarkIdentity("b", 1, "f", "c", "r", "other", "p", "m"), 0.5, "ms")
    assert not service.compare_benchmark(target, changed).comparable
