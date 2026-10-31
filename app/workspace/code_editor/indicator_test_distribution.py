"""Host-managed indicator reference test-data distribution and verification.

Description:
    Implements fail-closed indicator test-data bundle installation
    (WO-CE-TEST-DISTRIBUTION). Rejects legacy unauthenticated donor endpoints,
    enforces concurrency guards against running indicator suites, verifies SHA-256
    digests and archive structure bounds, and atomically installs reference CSVs
    and IndicatorTester.xml.
Purpose:
    FEAT-CODE-EDITOR-TEST-DISTRIBUTION: Provide safe, checksum-verified indicator
    reference test-data installation with durable progress reporting.
Key Capabilities:
    - FR-code-editor-test-distribution-start: Enforce concurrency and trust gates
      before starting test-data bundle verification and installation.
    - FR-code-editor-test-distribution-verify: Validate SHA-256 digest, zip safety,
      and allowed reference file extensions before atomic publication.
    - FR-code-editor-test-distribution-status: Persist and report progress and
      terminal status (TestsDownloadStatus parity).
Python API Usage:
    from app.workspace.code_editor.indicator_test_distribution import (
        IndicatorTestDistributionService,
    )
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor/test_indicator_suite.py --no-cov
"""

from __future__ import annotations

import hashlib
import logging
import threading
import urllib.request
import uuid
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath

from pydantic import ValidationError

from app.core.jobs.manager import JobManager
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._storage import StateStore, atomic_write_batch
from app.workspace.code_editor.command_models import (
    SuiteLoadConfigRequest,
    TestDistributionRequest,
    TestDistributionSnapshot,
)
from app.workspace.code_editor.indicator_suite import (
    SUPPORTED_SUITE_ENGINES,
    IndicatorSuiteService,
    suite_config_from_xml,
)

logger = logging.getLogger(__name__)

MAX_ARCHIVE_BYTES = 25 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 1000
MAX_COMPRESSION_RATIO = 100.0
FORBIDDEN_DONOR_HOST = "autoupdate.strategyquant.com"


class IndicatorTestDistributionService:
    """Install verified indicator reference test bundles into the suite directory."""

    def __init__(
        self,
        manager: JobManager,
        store: StateStore,
        suite_service: IndicatorSuiteService,
    ) -> None:
        logger.debug("FR-code-editor-test-distribution-start: service initialized")
        self.manager = manager
        self.store = store
        self.suite_service = suite_service
        self._lock = threading.RLock()
        self._active_job_id: str | None = None

    def download_tests(self, req: TestDistributionRequest) -> TestDistributionSnapshot:
        """Validate source and install verified indicator reference test bundle."""
        logger.debug("FR-code-editor-test-distribution-start: invoked")
        with self._lock:
            if self.suite_service.is_running:
                raise CodeEditorError(
                    "Indicator tests are running. Please wait until the tests "
                    "finish or stop the execution and try again.",
                    code=ErrorCode.CONFLICT,
                )
            if self._active_job_id is not None:
                raise CodeEditorError(
                    "Test data download is already in progress",
                    code=ErrorCode.CONFLICT,
                )
            if not req.archive_path and not req.source_url:
                raise CodeEditorError(
                    "Provide an approved local archive_path or trusted HTTPS source_url"
                )
            if req.source_url:
                lowered_url = req.source_url.strip().lower()
                if FORBIDDEN_DONOR_HOST in lowered_url or not lowered_url.startswith(
                    "https://"
                ):
                    raise CodeEditorError(
                        "Legacy donor URL and unencrypted HTTP sources are forbidden"
                    )

            job_id = "indy-dist-" + uuid.uuid4().hex
            self._active_job_id = job_id
            initial = TestDistributionSnapshot(
                job_id=job_id,
                status="RUNNING",
                progress=0.0,
                completed=False,
            )
            self._write_snapshot(initial)
            try:
                raw_bytes = self._load_archive_bytes(req)
                self._verify_digest(raw_bytes, req.expected_sha256)
                staged_files, xml_text = self._validate_and_stage_zip(raw_bytes)
                atomic_write_batch(staged_files)
                config_updated = False
                if xml_text is not None:
                    self.suite_service.load_config(
                        SuiteLoadConfigRequest(xml_content=xml_text)
                    )
                    config_updated = True
                else:
                    self.suite_service.load_config(SuiteLoadConfigRequest())
                installed_rel = sorted(
                    p.relative_to(self.suite_service.tests_dir).as_posix()
                    for p in staged_files
                )
                completed = TestDistributionSnapshot(
                    job_id=job_id,
                    status="COMPLETED",
                    progress=100.0,
                    completed=True,
                    error="",
                    installed_files=installed_rel,
                    config_updated=config_updated,
                )
                self._write_snapshot(completed)
                logger.info(
                    "FR-code-editor-test-distribution-verify: installed=%d",
                    len(installed_rel),
                )
                return completed
            except CodeEditorError as exc:
                failed = TestDistributionSnapshot(
                    job_id=job_id,
                    status="FAILED",
                    progress=0.0,
                    completed=False,
                    error=str(exc),
                )
                self._write_snapshot(failed)
                raise
            except Exception as exc:
                msg = "Failed to install indicator test bundle"
                failed = TestDistributionSnapshot(
                    job_id=job_id,
                    status="FAILED",
                    progress=0.0,
                    completed=False,
                    error=msg,
                )
                self._write_snapshot(failed)
                raise CodeEditorError(msg) from exc
            finally:
                self._active_job_id = None

    def get_status(self, job_id: str | None = None) -> TestDistributionSnapshot:
        """Return the latest or requested test-data distribution status."""
        logger.debug("FR-code-editor-test-distribution-status: invoked")
        key = (
            f"indicator_distribution:job:{job_id}"
            if job_id
            else "indicator_distribution:latest"
        )
        raw = self.store.read(key)
        if raw is None:
            if job_id is not None:
                raise CodeEditorError(
                    "Test distribution job not found", code=ErrorCode.NOT_FOUND
                )
            return TestDistributionSnapshot(
                job_id="idle", status="IDLE", progress=0.0, completed=False
            )
        try:
            return TestDistributionSnapshot.model_validate(raw)
        except ValidationError:
            raise CodeEditorError(
                "Invalid stored test distribution status", code=ErrorCode.INTERNAL
            ) from None

    def _load_archive_bytes(self, req: TestDistributionRequest) -> bytes:
        if req.archive_path:
            src = Path(req.archive_path).resolve()
            if not src.is_file():
                raise CodeEditorError(
                    f"Test bundle archive not found: {req.archive_path}"
                )
            size = src.stat().st_size
            if size > MAX_ARCHIVE_BYTES:
                raise CodeEditorError("Test bundle archive exceeds maximum size limit")
            return src.read_bytes()
        assert req.source_url is not None
        request = urllib.request.Request(  # noqa: S310
            req.source_url,
            headers={"User-Agent": "HaruQuantAI-TestDistribution/1.0"},
        )
        with urllib.request.urlopen(request, timeout=15.0) as resp:  # noqa: S310
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ARCHIVE_BYTES:
                    raise CodeEditorError(
                        "Downloaded bundle exceeds maximum size limit"
                    )
                chunks.append(chunk)
            return b"".join(chunks)

    def _verify_digest(self, payload: bytes, expected_sha256: str) -> None:
        actual = hashlib.sha256(payload).hexdigest().lower()
        if actual != expected_sha256.strip().lower():
            raise CodeEditorError(
                "Test bundle SHA-256 digest mismatch; refusing installation"
            )

    def _validate_and_stage_zip(
        self, payload: bytes
    ) -> tuple[dict[Path, bytes], str | None]:
        tests_root = self.suite_service.tests_dir.resolve()
        staged: dict[Path, bytes] = {}
        xml_text: str | None = None
        total_uncompressed = 0
        try:
            with zipfile.ZipFile(BytesIO(payload), "r") as zf:
                infos = [i for i in zf.infolist() if not i.is_dir()]
                if not infos:
                    raise CodeEditorError("Test bundle archive contains no files")
                if len(infos) > MAX_ARCHIVE_ENTRIES:
                    raise CodeEditorError("Test bundle exceeds maximum entry count")
                for info in infos:
                    rel_posix = PurePosixPath(info.filename.replace("\\", "/"))
                    if (
                        rel_posix.is_absolute()
                        or ".." in rel_posix.parts
                        or any(part.startswith(".") for part in rel_posix.parts)
                    ):
                        raise CodeEditorError(
                            f"Unsafe archive entry path: {info.filename}"
                        )
                    total_uncompressed += info.file_size
                    if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                        raise CodeEditorError(
                            "Test bundle uncompressed size exceeds limit"
                        )
                    compressed = max(info.compress_size, 1)
                    if (
                        info.file_size > 65536
                        and (info.file_size / compressed) > MAX_COMPRESSION_RATIO
                    ):
                        raise CodeEditorError(
                            "Archive compression ratio exceeds safety threshold"
                        )
                    parts = rel_posix.parts
                    if len(parts) == 1 and parts[0] == "IndicatorTester.xml":
                        data = zf.read(info)
                        xml_text = data.decode("utf-8")
                        suite_config_from_xml(xml_text)
                        dest = (tests_root / "IndicatorTester.xml").resolve()
                        staged[dest] = data
                    elif len(parts) == 1 and parts[0].lower().endswith(".csv"):
                        dest = (tests_root / parts[0]).resolve()
                        if not dest.is_relative_to(tests_root):
                            raise CodeEditorError("Entry escapes tests directory")
                        staged[dest] = zf.read(info)
                    elif (
                        len(parts) == 2
                        and parts[0] in SUPPORTED_SUITE_ENGINES
                        and parts[1].lower().endswith(".csv")
                    ):
                        dest = (tests_root / parts[0] / parts[1]).resolve()
                        if not dest.is_relative_to(tests_root):
                            raise CodeEditorError("Entry escapes tests directory")
                        staged[dest] = zf.read(info)
                    else:
                        raise CodeEditorError(
                            f"Unsupported test bundle entry: {info.filename}"
                        )
        except zipfile.BadZipFile as exc:
            raise CodeEditorError("Invalid ZIP archive for indicator tests") from exc
        return staged, xml_text

    def _write_snapshot(self, snapshot: TestDistributionSnapshot) -> None:
        payload = snapshot.model_dump(mode="json")
        if snapshot.job_id != "idle":
            self.store.write(f"indicator_distribution:job:{snapshot.job_id}", payload)
        self.store.write("indicator_distribution:latest", payload)
