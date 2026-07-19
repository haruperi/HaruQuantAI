"""Package-wide non-functional verification for Optimization."""

# ruff: noqa: INP001

from __future__ import annotations

import ast
import logging
import re
import subprocess
import sys
from pathlib import Path

import pytest
from app.services.optimization import OFFICIAL_OPTIMIZATION_TOOLS
from app.services.optimization.errors import OptimizationError
from app.services.optimization.evidence import (
    EvidenceAssemblyRequest,
    build_optimization_evidence,
    build_report_package,
)
from app.services.optimization.search import iter_grid_candidates, run_bounded_search
from app.services.optimization.validation import build_time_series_splits
from app.utils import canonical_json, logger
from tests.optimization.unit.test_search_contracts import search_request
from tests.optimization.unit.test_sweep import FakeAdapter
from tests.optimization.unit.test_validation_contracts import walk_forward_request

_ROOT = Path(__file__).parents[3]
_PACKAGE = _ROOT / "app" / "services" / "optimization"


class _RecordCollector(logging.Handler):
    """Capture structured Optimization log records for inspection."""

    def __init__(self) -> None:
        """Initialize an empty record buffer."""
        super().__init__(level=logging.INFO)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Store one emitted log record.

        Args:
            record: Structured record emitted by the system logger.
        """
        self.records.append(record)


def _capture_records() -> tuple[_RecordCollector, logging.Logger, int]:
    """Attach an in-memory handler to the system logger.

    Returns:
        Collector, logger, and prior logging level for restoration.
    """
    logger.debug("Capturing Optimization structured observability records")
    collector = _RecordCollector()
    domain_logger = logging.getLogger("haruquant")
    previous_level = domain_logger.level
    domain_logger.setLevel(logging.INFO)
    domain_logger.addHandler(collector)
    return collector, domain_logger, previous_level


def test_architecture_and_safety_import_boundaries() -> None:
    """Optimization imports public dependencies and no live-trading domain."""
    logger.debug("Testing Optimization architecture and safety boundaries")
    prohibited = {"app.services.brokers", "app.services.trading"}
    imported: set[str] = set()
    for path in _PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
    assert not any(
        name == prefix or name.startswith(f"{prefix}.")
        for name in imported
        for prefix in prohibited
    )
    assert not any(".storage" in name for name in imported if ".data" in name)


def test_deterministic_replay_and_serialization() -> None:
    """Replay preserves identities while excluding measured runtime from hashes."""
    logger.debug("Testing Optimization deterministic replay and JSON serialization")
    first = build_optimization_evidence(
        EvidenceAssemblyRequest(
            search=run_bounded_search(search_request(), FakeAdapter())
        )
    )
    second = build_optimization_evidence(
        EvidenceAssemblyRequest(
            search=run_bounded_search(search_request(), FakeAdapter())
        )
    )
    assert first.reproducibility_hash == second.reproducibility_hash
    assert tuple(item["candidate_hash"] for item in first.ranked_candidates) == tuple(
        item["candidate_hash"] for item in second.ranked_candidates
    )
    assert canonical_json(first.model_dump(mode="json"))


def test_fail_closed_limits_and_redacted_errors() -> None:
    """Cap failures stop work and controlled errors redact sensitive fields."""
    logger.debug("Testing Optimization failure and redaction policies")
    with pytest.raises(ValueError, match="configured cap"):
        tuple(
            iter_grid_candidates(
                search_request().space,
                max_candidates=1,
                max_expansion=20,
                max_constraints=5,
            )
        )
    payload = OptimizationError(
        "OPT_INVALID_REQUEST",
        safe_details={"authorization": "secret", "field": "period"},
    ).to_payload()
    assert "secret" not in canonical_json(payload)


def test_structured_observability_events_are_redacted() -> None:
    """Search events expose bounded operational facts without request payloads."""
    logger.debug("Testing Optimization structured observability events")
    collector, domain_logger, previous_level = _capture_records()
    try:
        request = search_request()
        summary = run_bounded_search(request, FakeAdapter())
        with pytest.raises(ValueError, match="configured cap"):
            tuple(
                iter_grid_candidates(
                    request.space,
                    max_candidates=1,
                    max_expansion=20,
                    max_constraints=5,
                )
            )
    finally:
        domain_logger.removeHandler(collector)
        domain_logger.setLevel(previous_level)

    completed = [
        record
        for record in collector.records
        if getattr(record, "event", None) == "optimization.search_completed"
    ]
    assert completed
    assert getattr(completed[-1], "request_id", None) == request.request_id
    assert getattr(completed[-1], "candidate_count", None) == len(summary.candidates)
    assert getattr(completed[-1], "duration_ms", -1) >= 0
    rejected = [
        record
        for record in collector.records
        if getattr(record, "event", None) == "optimization.cap_rejection"
    ]
    assert rejected
    assert getattr(rejected[-1], "candidate_count", None) == 2
    assert "execution_context" not in str(completed[-1].__dict__)


def test_import_is_side_effect_safe() -> None:
    """A clean interpreter imports Optimization without provider initialization."""
    logger.debug("Testing Optimization clean import behavior")
    command = (
        "import sys; import app.services.optimization; "
        "blocked={'MetaTrader5','ctrader_open_api'}; "
        "print(sorted(blocked.intersection(sys.modules)))"
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", command],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip().endswith("[]")


def test_trace_utc_compatibility_and_persistence_truth() -> None:
    """Traces propagate, times are UTC, API is fixed, and packages are advisory."""
    logger.debug(
        "Testing Optimization trace, time, compatibility, and durability truth"
    )

    class CapturingAdapter(FakeAdapter):
        """Adapter that records every complete candidate request."""

        def __init__(self) -> None:
            """Initialize an empty captured request sequence."""
            self.requests = []

        def execute(self, request):
            """Capture and delegate deterministic execution."""
            self.requests.append(request)
            return super().execute(request)

    adapter = CapturingAdapter()
    summary = run_bounded_search(search_request(), adapter)
    assert len({item.request_id for item in adapter.requests}) == len(adapter.requests)
    assert all(
        item.workflow_id == search_request().workflow_id for item in adapter.requests
    )
    assert all(
        boundary.utcoffset() is not None and boundary.utcoffset().total_seconds() == 0
        for split in build_time_series_splits(walk_forward_request())
        for boundary in (
            split.train_start,
            split.train_end,
            split.test_start,
            split.test_end,
        )
    )
    result = build_optimization_evidence(EvidenceAssemblyRequest(search=summary))
    assert "durable" not in build_report_package(result)
    assert OFFICIAL_OPTIMIZATION_TOOLS == (
        "build_optimization_handoff",
        "calculate_parameter_stability",
        "calculate_robustness_score",
        "compare_optimization_runs",
        "detect_overfit_parameters",
        "rank_parameter_sets",
        "run_parameter_sweep",
        "run_robustness_analysis",
        "run_walk_forward_matrix",
        "run_walk_forward_optimization",
    )


def test_requirement_traceability_is_complete() -> None:
    """Every FR is unique and every named unit/usage test exists at its path."""
    logger.debug("Testing Optimization requirement traceability")
    readme = (_PACKAGE / "README.md").read_text(encoding="utf-8")
    ids = [f"FR-OPT-{index:03d}" for index in range(1, 65)]
    assert all(readme.count(f"`{item}`") == 1 for item in ids)
    references = re.findall(
        r"(tests/optimization/(?:unit|usage)/[^`()<>, ]+\.py)::"
        r"(test_[A-Za-z0-9_]+)",
        readme,
    )
    for relative_path, function_name in references:
        path = _ROOT / relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"))
        actual = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert function_name in actual
