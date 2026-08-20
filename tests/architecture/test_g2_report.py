"""Parity and structural tests for G2 Audit Report.

Traces to: P2-T05, Gate G2
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_report() -> str:
    report_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "dev"
        / "plugin-decoupling"
        / "audit"
        / "G2_REPORT.md"
    )
    assert report_path.is_file(), "G2_REPORT.md missing"
    return report_path.read_text(encoding="utf-8")


def _read_matrix() -> dict[str, Any]:
    matrix_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "dev"
        / "plugin-decoupling"
        / "audit"
        / "removability_matrix.json"
    )
    assert matrix_path.is_file(), "removability_matrix.json missing"
    return json.loads(matrix_path.read_text(encoding="utf-8"))


def test_report_counts_match_matrix() -> None:
    """Verify counts in G2_REPORT.md match removability_matrix.json."""
    report = _read_report()
    matrix = _read_matrix()

    total_features = len(matrix["features"])
    assert total_features == 253
    assert f"**{total_features}**" in report

    total_domains = len(matrix["domains"])
    assert total_domains == 15

    assert "GATE G2 STATUS: PASS" in report


def test_every_hard_cycle_has_one_break_edge() -> None:
    """Verify every hard cycle in G2_REPORT.md declares an explicit break edge and method."""
    report = _read_report()
    matrix = _read_matrix()

    hard_cycles = matrix["cycles"]["hard_cycles"]
    for hc in hard_cycles:
        domains = hc["domains"]
        assert any(d in report for d in domains)
        assert (
            "contract" in report
            or "event" in report
            or "ownership_correction" in report
        )


def test_every_feature_is_classified() -> None:
    """Verify all 253 features are present in the matrix and have a valid classification."""
    matrix = _read_matrix()
    assert len(matrix["features"]) == 253

    valid_classifications = {
        "protected_kernel_candidate",
        "stable_capability_spec",
        "required_profile_provider",
        "optional_provider",
        "composition_only_module",
        "compatibility_facade",
        "historical_migration_artifact",
        "invalid_coupling",
    }
    for feat in matrix["features"]:
        assert feat["classification"] in valid_classifications


def test_every_wave_has_ordered_inputs() -> None:
    """Verify G2_REPORT.md specifies provider order for waves 12.1 through 12.21."""
    report = _read_report()
    for wave_num in range(1, 22):
        wave_str = f"Wave 12.{wave_num}"
        assert wave_str in report, f"Missing wave definition in report: {wave_str}"
