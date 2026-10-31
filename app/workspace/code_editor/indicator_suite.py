"""Batch indicator suite configuration, XML interchange, and execution service.

Description:
    Implements the multi-indicator reference test suite workflow (WO-CE-INDICATOR-SUITE)
    with donor XML interchange, multi-output indicator discovery, positional and named
    parameter coercion, 7-column semicolon CSV reference loading, shift and warmup bar
    alignment, strict 10**(-decimals) comparison, and cooperative JobManager execution.
Purpose:
    FEAT-CODE-EDITOR-INDICATOR-SUITE: Deliver donor-faithful batch indicator testing
    while preserving single-indicator studio defaults and host job ownership.
Key Capabilities:
    - FR-code-editor-suite-list-indicators: Expand indicator classes and output buffers
      for suite selection with deterministic logging.
    - FR-code-editor-suite-config: Create, add, load, and save suite configurations in
      both JSON state and donor XML format.
    - FR-code-editor-suite-execute: Run reference CSV comparisons with shift, warmup,
      strict decimal tolerance, 150-difference cap, and cooperative cancellation.
Python API Usage:
    from app.workspace.code_editor.indicator_suite import IndicatorSuiteService
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor/test_indicator_suite.py --no-cov
"""

from __future__ import annotations

import logging
import math
import threading
import uuid
from pathlib import Path
from typing import Literal, cast

import numpy as np
from pydantic import ValidationError

from app.core.jobs.manager import JobCancelledError, JobContext, JobManager
from app.core.lib.responses import ErrorCode
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.price import BarPrice
from app.workspace.code_editor._common import PROJECT_ROOT, CodeEditorError
from app.workspace.code_editor._indicator_data import (
    calculate_indicator,
    indicator_defaults,
    output_series,
)
from app.workspace.code_editor._indicator_resolver import resolve_indicator
from app.workspace.code_editor._indicator_suite_io import (
    MAX_INVALID_LINES,
    SUPPORTED_SUITE_ENGINES,
    ReferenceBarRow,
    _coerce_scalar,
    _resolve_reference_file,
    default_reference_filename,
    format_default_parameters,
    parse_reference_csv,
    parse_suite_parameters,
    suite_config_from_xml,
    suite_config_to_xml,
)
from app.workspace.code_editor._storage import StateStore, atomic_write_batch
from app.workspace.code_editor.catalogue import indicator_catalogue
from app.workspace.code_editor.command_models import (
    SuiteAddTestsRequest,
    SuiteConfigModel,
    SuiteCreateConfigRequest,
    SuiteIndicatorOption,
    SuiteLoadConfigRequest,
    SuiteSaveConfigRequest,
    SuiteSnapshot,
    SuiteStartRequest,
    SuiteTestCaseModel,
)

logger = logging.getLogger(__name__)

MAX_REPORTED_DIFFERENCES = 150
TERMINAL_SUITE_STATUSES = {"COMPLETED", "STOPPED", "FAILED", "INTERRUPTED"}
DEFAULT_TESTS_ROOT = PROJECT_ROOT / "data" / "indicator_tests"

__all__ = [
    "DEFAULT_TESTS_ROOT",
    "MAX_INVALID_LINES",
    "MAX_REPORTED_DIFFERENCES",
    "SUPPORTED_SUITE_ENGINES",
    "TERMINAL_SUITE_STATUSES",
    "IndicatorSuiteService",
    "ReferenceBarRow",
    "_coerce_scalar",
    "default_reference_filename",
    "format_default_parameters",
    "list_suite_indicators",
    "parse_reference_csv",
    "parse_suite_parameters",
    "resolve_suite_indicator",
    "run_single_suite_test",
    "suite_config_from_xml",
    "suite_config_to_xml",
]


def list_suite_indicators() -> list[SuiteIndicatorOption]:
    """Expand registered indicators across their declared output buffers."""
    logger.debug("FR-code-editor-suite-list-indicators: invoked")
    options: list[SuiteIndicatorOption] = []
    for item in indicator_catalogue():
        outputs = item.outputs or ["value"]
        default_param_str = format_default_parameters(item.parameters)
        for index, output_name in enumerate(outputs):
            is_primary = index == 0 and (
                len(outputs) == 1 or output_name.lower() in {"value", "main"}
            )
            indicator_label = item.name if is_primary else f"{item.name}.{output_name}"
            identity = item.identity if is_primary else f"{item.identity}.{output_name}"
            options.append(
                SuiteIndicatorOption(
                    identity=identity,
                    indicator=indicator_label,
                    class_name=item.name,
                    output=output_name,
                    file_path=item.file_path,
                    default_parameters=default_param_str,
                    parameters=item.parameters,
                    protected=item.protected,
                )
            )
    logger.info("FR-code-editor-suite-list-indicators: count=%d", len(options))
    return options


def resolve_suite_indicator(
    indicator_ref: str,
) -> tuple[type[BaseIndicator], str | None]:
    """Resolve an indicator class and optional output buffer from a suite reference."""
    cleaned = indicator_ref.strip()
    if not cleaned:
        raise CodeEditorError("Indicator reference must not be empty")
    if "::" in cleaned:
        file_part, class_and_output = cleaned.split("::", 1)
        if "." in class_and_output:
            class_name, output_name = class_and_output.split(".", 1)
            return resolve_indicator(f"{file_part}::{class_name}"), output_name
        return resolve_indicator(cleaned), None
    if "." in cleaned and not cleaned.endswith(".py"):
        class_name, output_name = cleaned.split(".", 1)
        return resolve_indicator(class_name), output_name
    return resolve_indicator(cleaned), None


def run_single_suite_test(
    test: SuiteTestCaseModel,
    *,
    engine: str,
    bars_to_reserve: int,
    tests_dir: Path,
) -> SuiteTestCaseModel:
    """Execute one indicator suite test case against its reference CSV file."""
    ref_path = _resolve_reference_file(tests_dir, engine, test.file_name)
    exists = ref_path.is_file()
    if not exists:
        return test.model_copy(
            update={
                "exists": False,
                "result": "Skipped - File not found.",
                "show_grid": False,
                "errors": [],
            }
        )
    valid_rows, invalid_lines = parse_reference_csv(ref_path)
    if invalid_lines:
        return test.model_copy(
            update={
                "exists": True,
                "result": f"Skipped - File contains invalid lines ({len(invalid_lines)})",
                "show_grid": False,
                "errors": invalid_lines[:MAX_INVALID_LINES],
            }
        )
    if not valid_rows:
        return test.model_copy(
            update={
                "exists": True,
                "result": "Skipped - Empty file.",
                "show_grid": False,
                "errors": [],
            }
        )
    start_idx = max(bars_to_reserve, test.shift)
    if len(valid_rows) <= start_idx:
        return test.model_copy(
            update={
                "exists": True,
                "result": "Skipped - Insufficient bars for reserve/shift.",
                "show_grid": False,
                "errors": [],
            }
        )
    try:
        cls, target_output = resolve_suite_indicator(test.indicator)
        params = parse_suite_parameters(cls, test.parameters)
        bars = BarPrice(
            open_data=np.asarray([r.open_price for r in valid_rows], dtype=np.float64),
            high_data=np.asarray([r.high_price for r in valid_rows], dtype=np.float64),
            low_data=np.asarray([r.low_price for r in valid_rows], dtype=np.float64),
            close_data=np.asarray(
                [r.close_price for r in valid_rows], dtype=np.float64
            ),
            volume_data=np.asarray([r.volume for r in valid_rows], dtype=np.float64),
        )
        timestamps = [r.timestamp for r in valid_rows]
        outputs = output_series(
            calculate_indicator(cls, bars, params, timestamps), len(valid_rows)
        )
        selected_series = _select_output_series(outputs, target_output)
    except Exception as exc:
        msg = (
            str(exc)
            if isinstance(exc, CodeEditorError)
            else "Indicator calculation failed"
        )
        return test.model_copy(
            update={
                "exists": True,
                "result": f"Failed - {msg}",
                "show_grid": False,
                "errors": [msg],
            }
        )

    tolerance = 10.0 ** (-test.decimals)
    mismatches: list[str] = []
    diff_count = 0
    for idx in range(start_idx, len(valid_rows)):
        actual = float(selected_series[idx - test.shift])
        reference = valid_rows[idx].reference_value
        is_match = (
            math.isfinite(actual)
            and math.isfinite(reference)
            and abs(actual - reference) < tolerance
        )
        if not is_match:
            diff_count += 1
            if len(mismatches) < MAX_REPORTED_DIFFERENCES:
                actual_str = (
                    f"{actual:.{test.decimals}f}" if math.isfinite(actual) else "NaN"
                )
                ref_str = (
                    f"{reference:.{test.decimals}f}"
                    if math.isfinite(reference)
                    else "NaN"
                )
                mismatches.append(f"{valid_rows[idx].raw_time},{actual_str},{ref_str}")
            if diff_count > MAX_REPORTED_DIFFERENCES:
                return test.model_copy(
                    update={
                        "exists": True,
                        "result": f"Failed - more than {MAX_REPORTED_DIFFERENCES} differences",
                        "show_grid": True,
                        "errors": mismatches,
                    }
                )
    if diff_count == 0:
        return test.model_copy(
            update={
                "exists": True,
                "result": "Passed",
                "show_grid": False,
                "errors": [],
            }
        )
    return test.model_copy(
        update={
            "exists": True,
            "result": f"Failed - {diff_count} differences",
            "show_grid": True,
            "errors": mismatches,
        }
    )


def _select_output_series(
    outputs: dict[str, np.typing.NDArray[np.float64]], target_output: str | None
) -> np.typing.NDArray[np.float64]:
    """Select the requested output buffer or primary output series."""
    if target_output is None:
        return next(iter(outputs.values()))
    if target_output in outputs:
        return outputs[target_output]
    lowered = target_output.lower()
    for name, series in outputs.items():
        if name.lower() == lowered:
            return series
    if lowered in {"value", "main"} and len(outputs) == 1:
        return next(iter(outputs.values()))
    raise CodeEditorError(f"Unknown indicator output buffer '{target_output}'")


class IndicatorSuiteService:
    """Manage batch indicator suite configs, XML persistence, and background runs."""

    def __init__(
        self,
        manager: JobManager,
        store: StateStore,
        tests_dir: Path | None = None,
    ) -> None:
        logger.debug("FR-code-editor-suite-config: service initialized")
        self.manager = manager
        self.store = store
        self.tests_dir = (tests_dir or DEFAULT_TESTS_ROOT).resolve()
        if store.gateway.ensure_jobs_schema()["success"] is not True:
            raise CodeEditorError(
                "Host job storage is unavailable or incompatible",
                code=ErrorCode.UNAVAILABLE,
            )
        self._lock = threading.RLock()
        self._active_job_id: str | None = None

    @property
    def is_running(self) -> bool:
        """Return whether a batch indicator test suite is currently running."""
        with self._lock:
            if self._active_job_id is None:
                return False
            record = self.manager.get_job(self._active_job_id)
            if record is not None and record.status in {
                "COMPLETED",
                "FAILED",
                "CANCELLED",
                "INTERRUPTED",
            }:
                self._active_job_id = None
                return False
            return True

    def create_new_config(self, req: SuiteCreateConfigRequest) -> SuiteSnapshot:
        """Create a new suite config with optional initial indicator tests."""
        logger.debug("FR-code-editor-suite-config: create_new_config invoked")
        if req.engine not in SUPPORTED_SUITE_ENGINES:
            raise CodeEditorError(f"Unsupported indicator suite engine: {req.engine}")
        tests = self._build_test_rows(
            req.indicators,
            existing=[],
            engine=req.engine,
            allow_duplicates=False,
        )
        config = SuiteConfigModel(
            engine=req.engine,
            bars_to_reserve=req.bars_to_reserve,
            tests=tests,
        )
        return self._persist_config_snapshot(config, message="Created suite config")

    def add_tests(self, req: SuiteAddTestsRequest) -> SuiteSnapshot:
        """Append indicator tests to the current suite config."""
        logger.debug("FR-code-editor-suite-config: add_tests invoked")
        current = self.load_config(SuiteLoadConfigRequest()).config
        new_rows = self._build_test_rows(
            req.indicators,
            existing=current.tests,
            engine=current.engine,
            allow_duplicates=req.allow_duplicates,
        )
        updated = current.model_copy(update={"tests": [*current.tests, *new_rows]})
        return self._persist_config_snapshot(
            updated, message=f"Added {len(new_rows)} indicator test(s)"
        )

    def load_config(self, req: SuiteLoadConfigRequest) -> SuiteSnapshot:
        """Load suite configuration from explicit XML, stored state, or disk XML."""
        logger.debug("FR-code-editor-suite-config: load_config invoked")
        if req.xml_content is not None:
            config = suite_config_from_xml(req.xml_content, tests_dir=self.tests_dir)
            return self._persist_config_snapshot(
                config, message="Loaded suite config from XML"
            )
        raw = self.store.read("indicator_suite:config")
        if raw is not None:
            try:
                config = SuiteConfigModel.model_validate(raw)
                refreshed = self._refresh_file_existence(config)
                return self._build_idle_snapshot(
                    refreshed, "Loaded stored suite config"
                )
            except ValidationError:
                raise CodeEditorError(
                    "Invalid stored indicator suite configuration",
                    code=ErrorCode.INTERNAL,
                ) from None
        xml_path = self.tests_dir / "IndicatorTester.xml"
        if xml_path.is_file():
            config = suite_config_from_xml(
                xml_path.read_text(encoding="utf-8"), tests_dir=self.tests_dir
            )
            return self._persist_config_snapshot(
                config, message="Loaded suite config from IndicatorTester.xml"
            )
        default_cfg = SuiteConfigModel()
        return self._persist_config_snapshot(
            default_cfg, message="Initialized default suite config"
        )

    def save_config(self, req: SuiteSaveConfigRequest) -> SuiteSnapshot:
        """Persist suite configuration in host storage and IndicatorTester.xml."""
        logger.debug("FR-code-editor-suite-config: save_config invoked")
        if req.xml_content is not None:
            config = suite_config_from_xml(req.xml_content, tests_dir=self.tests_dir)
        elif req.config is not None:
            if req.config.engine not in SUPPORTED_SUITE_ENGINES:
                raise CodeEditorError(
                    f"Unsupported indicator suite engine: {req.config.engine}"
                )
            config = self._refresh_file_existence(req.config)
        else:
            raise CodeEditorError("Provide either config or xml_content to save")
        return self._persist_config_snapshot(config, message="Saved suite config")

    def start_testing(self, req: SuiteStartRequest) -> SuiteSnapshot:
        """Start cooperative background execution of the indicator test suite."""
        logger.debug("FR-code-editor-suite-execute: start_testing invoked")
        with self._lock:
            if self.is_running:
                raise CodeEditorError(
                    "Indicator suite tests are already running",
                    code=ErrorCode.CONFLICT,
                )
            if req.config is not None:
                config = self.save_config(
                    SuiteSaveConfigRequest(config=req.config)
                ).config
            else:
                config = self.load_config(SuiteLoadConfigRequest()).config
            selected = [t for t in config.tests if (t.use or not req.selected_only)]
            if not selected:
                raise CodeEditorError("No indicator suite tests selected for execution")
            job_id = "indy-suite-" + uuid.uuid4().hex
            snapshot = SuiteSnapshot(
                job_id=job_id,
                status="QUEUED",
                status_code=1,
                progress=0.0,
                completed_tests=0,
                total_tests=len(selected),
                config=config,
                xml_content=suite_config_to_xml(config),
                message="Indicator suite queued",
            )
            self._write_snapshot(snapshot)
            self._active_job_id = job_id
            try:
                self.manager.submit_job(
                    self._execute_suite,
                    config,
                    req.selected_only,
                    job_id=job_id,
                    owner="code_editor",
                    kind="indicator_suite",
                    executor_kind="thread",
                    pass_context=True,
                )
            except Exception:
                self._active_job_id = None
                failed = snapshot.model_copy(
                    update={
                        "status": "FAILED",
                        "status_code": 4,
                        "message": "Indicator suite submission failed",
                    }
                )
                self._write_snapshot(failed)
                raise CodeEditorError(
                    "Indicator suite execution unavailable",
                    code=ErrorCode.UNAVAILABLE,
                ) from None
            logger.info("FR-code-editor-suite-execute: started job_id=%s", job_id)
            return snapshot

    def stop_testing(self, job_id: str | None = None) -> SuiteSnapshot:
        """Request cooperative cancellation of the active indicator test suite."""
        logger.debug("FR-code-editor-suite-execute: stop_testing invoked")
        with self._lock:
            snapshot = self.get_snapshot(job_id)
            if (
                snapshot.status not in TERMINAL_SUITE_STATUSES
                and snapshot.status != "IDLE"
            ):
                self.manager.cancel_job(snapshot.job_id)
                snapshot = snapshot.model_copy(
                    update={
                        "cancellation_requested": True,
                        "message": "Stop requested; finishing current indicator test",
                    }
                )
                self._write_snapshot(snapshot)
            logger.info("FR-code-editor-suite-execute: stop requested")
            return snapshot

    def get_snapshot(self, job_id: str | None = None) -> SuiteSnapshot:
        """Read the latest or requested suite execution snapshot."""
        with self._lock:
            key = (
                f"indicator_suite:job:{job_id}" if job_id else "indicator_suite:latest"
            )
            raw = self.store.read(key)
            if raw is None:
                if job_id is not None:
                    raise CodeEditorError(
                        "Indicator suite job not found", code=ErrorCode.NOT_FOUND
                    )
                return self.load_config(SuiteLoadConfigRequest())
            try:
                snapshot = SuiteSnapshot.model_validate(raw)
            except ValidationError:
                raise CodeEditorError(
                    "Invalid stored indicator suite snapshot",
                    code=ErrorCode.INTERNAL,
                ) from None
            record = self.manager.get_job(snapshot.job_id)
            if (
                snapshot.status not in TERMINAL_SUITE_STATUSES
                and snapshot.status != "IDLE"
            ):
                if record is not None and record.status == "CANCELLED":
                    snapshot = snapshot.model_copy(
                        update={
                            "status": "STOPPED",
                            "status_code": 4,
                            "cancellation_requested": True,
                            "message": "Indicator suite stopped",
                        }
                    )
                    self._write_snapshot(snapshot)
                    self._active_job_id = None
                elif record is not None and record.status in {"FAILED", "INTERRUPTED"}:
                    snapshot = snapshot.model_copy(
                        update={
                            "status": cast(
                                "Literal['FAILED', 'INTERRUPTED']", record.status
                            ),
                            "status_code": 4,
                            "message": "Indicator suite interrupted or failed",
                        }
                    )
                    self._write_snapshot(snapshot)
                    self._active_job_id = None
                elif snapshot.job_id != self._active_job_id:
                    snapshot = snapshot.model_copy(
                        update={
                            "status": "INTERRUPTED",
                            "status_code": 4,
                            "message": "Indicator suite interrupted by host restart",
                        }
                    )
                    self._write_snapshot(snapshot)
            return snapshot

    def _execute_suite(
        self, ctx: JobContext, config: SuiteConfigModel, selected_only: bool
    ) -> None:
        working_tests = list(config.tests)
        target_indices = [
            i for i, row in enumerate(working_tests) if row.use or not selected_only
        ]
        total = len(target_indices)
        passed = 0
        failed = 0
        skipped = 0
        snapshot = SuiteSnapshot(
            job_id=ctx.job_id,
            status="RUNNING",
            status_code=1,
            progress=0.0,
            completed_tests=0,
            total_tests=total,
            config=config,
            xml_content=suite_config_to_xml(config),
            message="Running indicator suite",
        )
        self._write_snapshot(snapshot)
        try:
            for step, row_idx in enumerate(target_indices):
                ctx.raise_if_cancelled()
                row = working_tests[row_idx]
                ctx.report_progress(
                    100.0 * step / max(total, 1), f"Testing {row.indicator}"
                )
                updated_row = run_single_suite_test(
                    row,
                    engine=config.engine,
                    bars_to_reserve=config.bars_to_reserve,
                    tests_dir=self.tests_dir,
                )
                working_tests[row_idx] = updated_row
                if updated_row.result == "Passed":
                    passed += 1
                elif updated_row.result.startswith("Skipped"):
                    skipped += 1
                else:
                    failed += 1
                updated_cfg = config.model_copy(update={"tests": list(working_tests)})
                xml_str = suite_config_to_xml(updated_cfg)
                self._persist_config_only(updated_cfg, xml_str)
                snapshot = SuiteSnapshot(
                    job_id=ctx.job_id,
                    status="RUNNING",
                    status_code=1,
                    progress=100.0 * (step + 1) / max(total, 1),
                    completed_tests=step + 1,
                    total_tests=total,
                    passed_tests=passed,
                    failed_tests=failed,
                    skipped_tests=skipped,
                    cancellation_requested=ctx.is_cancelled(),
                    message=f"Completed {step + 1} of {total} test(s)",
                    config=updated_cfg,
                    xml_content=xml_str,
                )
                self._write_snapshot(snapshot)
                ctx.raise_if_cancelled()
            snapshot = snapshot.model_copy(
                update={
                    "status": "COMPLETED",
                    "status_code": 3,
                    "progress": 100.0,
                    "message": (
                        f"Completed: {passed} passed, {failed} failed, {skipped} skipped"
                    ),
                }
            )
        except JobCancelledError:
            snapshot = snapshot.model_copy(
                update={
                    "status": "STOPPED",
                    "status_code": 4,
                    "cancellation_requested": True,
                    "message": "Indicator suite stopped by user",
                }
            )
        except Exception:
            logger.error("FR-code-editor-suite-execute: suite execution failed")
            snapshot = snapshot.model_copy(
                update={
                    "status": "FAILED",
                    "status_code": 4,
                    "message": "Indicator suite execution failed",
                }
            )
        finally:
            with self._lock:
                try:
                    if ctx.is_cancelled() and snapshot.status != "STOPPED":
                        snapshot = snapshot.model_copy(
                            update={
                                "status": "STOPPED",
                                "status_code": 4,
                                "cancellation_requested": True,
                                "message": "Indicator suite stopped by user",
                            }
                        )
                    self._write_snapshot(snapshot)
                finally:
                    self._active_job_id = None

    def _build_test_rows(
        self,
        indicators: list[str],
        *,
        existing: list[SuiteTestCaseModel],
        engine: str,
        allow_duplicates: bool,
    ) -> list[SuiteTestCaseModel]:
        rows: list[SuiteTestCaseModel] = []
        seen_signatures = {
            (r.indicator, r.parameters, r.shift, r.file_name) for r in existing
        }
        next_index = len(existing) + 1
        for raw_ref in indicators:
            cls, output_name = resolve_suite_indicator(raw_ref)
            defaults = indicator_defaults(cls)
            params_str = format_default_parameters(defaults)
            label = (
                cls.__name__
                if output_name is None or output_name.lower() in {"value", "main"}
                else f"{cls.__name__}.{output_name}"
            )
            file_name = default_reference_filename(label, params_str)
            signature = (label, params_str, 0, file_name)
            if not allow_duplicates and signature in seen_signatures:
                raise CodeEditorError(
                    f"Duplicate indicator test row for '{label}'",
                    code=ErrorCode.CONFLICT,
                )
            seen_signatures.add(signature)
            exists = _resolve_reference_file(
                self.tests_dir, engine, file_name
            ).is_file()
            rows.append(
                SuiteTestCaseModel(
                    test_id=f"test-{next_index}",
                    use=True,
                    indicator=label,
                    parameters=params_str,
                    decimals=6,
                    result="",
                    shift=0,
                    file_name=file_name,
                    exists=exists,
                    show_grid=False,
                    errors=[],
                )
            )
            next_index += 1
        return rows

    def _refresh_file_existence(self, config: SuiteConfigModel) -> SuiteConfigModel:
        updated_tests = [
            row.model_copy(
                update={
                    "exists": _resolve_reference_file(
                        self.tests_dir, config.engine, row.file_name
                    ).is_file()
                }
            )
            for row in config.tests
        ]
        return config.model_copy(update={"tests": updated_tests})

    def _persist_config_only(self, config: SuiteConfigModel, xml_str: str) -> None:
        self.store.write("indicator_suite:config", config.model_dump(mode="json"))
        self.store.write("indicator_suite:xml", {"xml": xml_str})
        xml_path = self.tests_dir / "IndicatorTester.xml"
        atomic_write_batch({xml_path: xml_str.encode("utf-8")})

    def _persist_config_snapshot(
        self, config: SuiteConfigModel, *, message: str
    ) -> SuiteSnapshot:
        refreshed = self._refresh_file_existence(config)
        xml_str = suite_config_to_xml(refreshed)
        with self._lock:
            self._persist_config_only(refreshed, xml_str)
            snapshot = self._build_idle_snapshot(refreshed, message, xml_str=xml_str)
            self._write_snapshot(snapshot)
            return snapshot

    def _build_idle_snapshot(
        self,
        config: SuiteConfigModel,
        message: str,
        *,
        xml_str: str | None = None,
    ) -> SuiteSnapshot:
        xml_payload = xml_str if xml_str is not None else suite_config_to_xml(config)
        passed = sum(1 for t in config.tests if t.result == "Passed")
        skipped = sum(1 for t in config.tests if t.result.startswith("Skipped"))
        failed = sum(
            1
            for t in config.tests
            if t.result and t.result != "Passed" and not t.result.startswith("Skipped")
        )
        return SuiteSnapshot(
            job_id="idle",
            status="IDLE",
            status_code=0,
            progress=0.0,
            completed_tests=passed + failed + skipped,
            total_tests=len(config.tests),
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            cancellation_requested=False,
            message=message,
            config=config,
            xml_content=xml_payload,
        )

    def _write_snapshot(self, snapshot: SuiteSnapshot) -> None:
        payload = snapshot.model_dump(mode="json")
        if snapshot.job_id != "idle":
            self.store.write(f"indicator_suite:job:{snapshot.job_id}", payload)
        self.store.write("indicator_suite:latest", payload)
