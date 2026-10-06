"""Test independent fixture observations and truthful runtime boundaries.

Description:
    Temporary copies of independently authored static cases exercise strict
    provenance and exact comparison; no runtime observation is manufactured.
Purpose:
    FEAT-HOST-EVIDENCE; DEC-HOST-P00-BOUNDED-FIXTURES and RELEASE-GATES.
Key Capabilities:
    - FR-HOST-EVIDENCE-FIXTURE-VALIDATION: Verify cases, failures and delivered logs.
      Associated: all tests; Logging: caplog asserts acceptance and error events.
Python API Usage:
    Run isolated tests with pytest; no runtime API is exposed.
CLI Usage:
    uv run pytest tests/unit/test_reference_fixtures.py --no-cov
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from tests.reference.fixtures import FIXTURE_FR, load_fixtures
from tests.reference.manifest import EvidenceError


@pytest.fixture
def fixtures(tmp_path: Path) -> Path:
    source = Path(__file__).parents[1] / "reference/p00-fixtures.json"
    path = tmp_path / "fixtures.json"
    path.write_bytes(source.read_bytes())
    return path


def test_static_fixture_success(
    fixtures: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    result = load_fixtures(fixtures)
    assert len(result.cases) == 2 and result.runtime_status == "unavailable"
    assert any(
        r.__dict__.get("fr_id") == FIXTURE_FR and r.levelno == logging.INFO
        for r in caplog.records
    )


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("version", "FIXTURE_INVALID"),
        ("duplicate", "FIXTURE_DUPLICATE"),
        ("timestamp", "FIXTURE_INVALID"),
        ("hash", "FIXTURE_INVALID"),
        ("runtime", "FIXTURE_PROVENANCE"),
        ("static_black_box", "FIXTURE_PROVENANCE"),
        ("mismatch", "FIXTURE_OBSERVATION"),
        ("missing_actual", "FIXTURE_INVALID"),
        ("null", "FIXTURE_OBSERVATION"),
        ("decisions", "FIXTURE_DECISIONS"),
        ("bad_decision", "FIXTURE_DECISIONS"),
        ("tolerance", "FIXTURE_INVALID"),
    ],
)
def test_fixture_rejection(fixtures: Path, mutation: str, code: str) -> None:  # noqa: C901 - explicit adversarial cases
    data = json.loads(fixtures.read_text())
    case = data["cases"][0]
    if mutation == "version":
        data["schema_version"] = 2
    elif mutation == "duplicate":
        data["cases"].append(case.copy())
    elif mutation == "timestamp":
        case["captured_at"] = "2026-10-06"
    elif mutation == "hash":
        case["artifact_sha256"] = "bad"
    elif mutation == "runtime":
        case["observation_kind"] = "runtime"
        case["inspection_method"] = "black_box"
    elif mutation == "static_black_box":
        case["inspection_method"] = "black_box"
    elif mutation == "mismatch":
        case["actual"] = -1
    elif mutation == "missing_actual":
        del case["actual"]
    elif mutation == "null":
        case["expected"] = None
        case["actual"] = None
    elif mutation == "decisions":
        case["decision_ids"] = []
    elif mutation == "bad_decision":
        case["decision_ids"] = ["DEC-UNREGISTERED"]
    else:
        case["tolerance"] = 0.01
    fixtures.write_text(json.dumps(data))
    with pytest.raises(EvidenceError, match=code):
        load_fixtures(fixtures)
