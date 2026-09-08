"""Public contract for bounded redacted diagnostics and benchmark comparison."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.contracts.workspace.models import DiagnosticBundleRef, WorkspaceRef


class DiagnosticStatus(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ProviderDiagnostic:
    capability: str
    generation: int | None
    status: DiagnosticStatus
    reason_code: str
    safe_detail: str = ""


@dataclass(frozen=True, slots=True)
class BenchmarkIdentity:
    benchmark_id: str
    benchmark_version: int
    fixture_hash: str
    build_commit: str
    runtime_id: str
    hardware_id: str
    resource_profile_id: str
    method_id: str


@dataclass(frozen=True, slots=True)
class BenchmarkMeasurement:
    identity: BenchmarkIdentity
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    comparable: bool
    target: BenchmarkMeasurement | None
    measurement: BenchmarkMeasurement | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiagnosticSnapshot:
    providers: tuple[ProviderDiagnostic, ...]
    truncated: bool
    captured_at: str


@runtime_checkable
class BuildDiagnosticsCapability(Protocol):
    def build_diagnostic_bundle(
        self,
        workspace: Path | WorkspaceRef,
        *,
        include_logs: bool = True,
        output_path: Path | None = None,
    ) -> DiagnosticBundleRef: ...

    def snapshot(self, providers: tuple[ProviderDiagnostic, ...]) -> DiagnosticSnapshot: ...

    def compare_benchmark(
        self,
        target: BenchmarkMeasurement | None,
        measurement: BenchmarkMeasurement | None,
    ) -> BenchmarkComparison: ...


__all__ = [
    "BenchmarkComparison", "BenchmarkIdentity", "BenchmarkMeasurement", "BuildDiagnosticsCapability",
    "DiagnosticSnapshot", "DiagnosticStatus", "ProviderDiagnostic",
]
