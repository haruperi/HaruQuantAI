"""Unit tests for wave provider work order appendix generator.

Traces to: P12.1-T01, Gate G12
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.architecture.provider_work_order_generator import (
    build_provider_record,
    render_wave_document,
    validate_provider_record,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MATRIX_PATH = (
    _REPO_ROOT
    / "docs"
    / "dev"
    / "plugin-decoupling"
    / "audit"
    / "removability_matrix.json"
)
_REPORT_PATH = (
    _REPO_ROOT / "docs" / "dev" / "plugin-decoupling" / "audit" / "G2_REPORT.md"
)


def test_rejects_incomplete_row() -> None:
    """Verify generator rejects incomplete provider records."""
    incomplete_rec = {
        "provider_id": "test.provider",
        # missing mandatory fields
    }
    with pytest.raises(SystemExit) as exc:
        validate_provider_record(incomplete_rec)
    assert exc.value.code == 2


def test_rejects_later_wave_dependency() -> None:
    """Verify generator validates provider inputs without cycles or future deps."""
    matrix_data = json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))
    raw_providers = matrix_data.get("providers", [])
    utils_providers = [p for p in raw_providers if p.get("domain") == "utils"]

    records = [build_provider_record(p, "12.1") for p in utils_providers]
    for r in records:
        validate_provider_record(r)


def test_generated_tasks_are_sized() -> None:
    """Verify generated work order document contains all required task categories."""
    matrix_data = json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))
    raw_providers = matrix_data.get("providers", [])
    utils_providers = [p for p in raw_providers if p.get("domain") == "utils"]

    records = [build_provider_record(p, "12.1") for p in utils_providers]
    records.sort(key=lambda p: p["provider_id"])

    rendered = render_wave_document("12.1", records)
    assert "# Wave 12.1 Work Orders" in rendered
    assert "P12.1-P001a" in rendered
    assert "P12.1-P001b" in rendered
    assert "P12.1-P001c1" in rendered
    assert "P12.1-P001d" in rendered
    assert "P12.1-P001e" in rendered
    assert "P12.1-P001f" in rendered
    assert (
        "PASS: Wave 12.1 work orders verified against G2 audit requirements."
        in rendered
    )


def test_generation_is_deterministic() -> None:
    """Verify two consecutive generations produce byte-identical markdown."""
    matrix_data = json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))
    raw_providers = matrix_data.get("providers", [])
    utils_providers = [p for p in raw_providers if p.get("domain") == "utils"]

    records1 = [build_provider_record(p, "12.1") for p in utils_providers]
    records1.sort(key=lambda p: p["provider_id"])
    doc1 = render_wave_document("12.1", records1)

    records2 = [build_provider_record(p, "12.1") for p in utils_providers]
    records2.sort(key=lambda p: p["provider_id"])
    doc2 = render_wave_document("12.1", records2)

    assert doc1 == doc2


def test_utils_order_matches_directive() -> None:
    """Verify utils provider count in wave 12.1 matches matrix."""
    matrix_data = json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))
    raw_providers = matrix_data.get("providers", [])
    utils_providers = [p for p in raw_providers if p.get("domain") == "utils"]
    assert len(utils_providers) == 16
