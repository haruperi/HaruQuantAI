"""Bounded redacted diagnostics and benchmark comparison."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import tempfile
import uuid
import zipfile

from app.contracts.workspace.build_diagnostics import (
    BenchmarkComparison, BenchmarkMeasurement, DiagnosticSnapshot, ProviderDiagnostic,
)
from app.contracts.workspace.models import DiagnosticBundleManifest, DiagnosticBundleRef, WorkspaceRef

_SECRET = re.compile(r"(?i)(authorization|password|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;]+")


class BuildDiagnosticsService:
    """Selected owner for safe Workspace diagnostics."""

    def __init__(self, max_records: int, max_bytes: int) -> None:
        self._max_records = max_records
        self._max_bytes = max_bytes
        self._closed = False

    def snapshot(self, providers: tuple[ProviderDiagnostic, ...]) -> DiagnosticSnapshot:
        self._ensure_open()
        truncated = len(providers) > self._max_records
        bounded = providers[: self._max_records]
        safe = tuple(ProviderDiagnostic(p.capability, p.generation, p.status, p.reason_code, self._redact(p.safe_detail)) for p in bounded)
        return DiagnosticSnapshot(safe, truncated, datetime.now(UTC).isoformat())

    def compare_benchmark(self, target: BenchmarkMeasurement | None, measurement: BenchmarkMeasurement | None) -> BenchmarkComparison:
        self._ensure_open()
        reasons: list[str] = []
        if target is None:
            reasons.append("TARGET_NOT_DECLARED")
        if measurement is None:
            reasons.append("MEASUREMENT_NOT_AVAILABLE")
        if target is not None and measurement is not None and target.identity != measurement.identity:
            reasons.append("BENCHMARK_IDENTITY_MISMATCH")
        if target is not None and measurement is not None and target.unit != measurement.unit:
            reasons.append("BENCHMARK_UNIT_MISMATCH")
        return BenchmarkComparison(not reasons, target, measurement, tuple(reasons))

    def build_diagnostic_bundle(self, workspace: Path | WorkspaceRef, *, include_logs: bool = True, output_path: Path | None = None) -> DiagnosticBundleRef:
        self._ensure_open()
        root = workspace.root_path if isinstance(workspace, WorkspaceRef) else Path(workspace)
        bundle_id = str(uuid.uuid4())
        created = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        logs: list[str] = []
        if include_logs and (root / "logs").is_dir():
            for path in sorted((root / "logs").glob("*.log")):
                if len(logs) >= self._max_records:
                    break
                try:
                    logs.extend(self._redact(line) for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[: self._max_records - len(logs)])
                except OSError:
                    logs.append("LOG_UNAVAILABLE")
        payload = {"bundle_id": bundle_id, "created_at": created, "workspace": root.name, "logs": logs, "truncated": len(logs) >= self._max_records}
        encoded = json.dumps(payload, sort_keys=True).encode()[: self._max_bytes]
        target = output_path or (Path(tempfile.gettempdir()) / f"haru-diagnostic-{bundle_id}.zip")
        if target.suffix.lower() != ".zip":
            target = target / f"diagnostic-{bundle_id}.zip"
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("diagnostics.json", encoded)
        archive_bytes = target.read_bytes()
        checksum = hashlib.sha256(archive_bytes).hexdigest()
        manifest = DiagnosticBundleManifest(
            bundle_id=bundle_id,
            created_at=created,
            build_version="v3",
            build_commit="runtime",
            schema_version=1,
            workspace_id=getattr(workspace, "workspace_id", None),
            log_entries_count=len(logs),
            job_records_count=0,
            integrity_findings=(),
            redaction_summary={"bounded": int(len(encoded) >= self._max_bytes)},
        )
        return DiagnosticBundleRef(bundle_id=bundle_id, archive_path=target, checksum_sha256=checksum, file_size_bytes=len(archive_bytes), manifest=manifest)

    def _redact(self, text: str) -> str:
        safe = _SECRET.sub(lambda match: match.group(1) + "=[REDACTED]", text)
        return safe[:4096]

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("build-diagnostics service is closed")

    def close(self) -> None:
        self._closed = True
