"""Requirement traceability tests for the analytics implementation matrix."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REQUIREMENTS_FILE = (
    PROJECT_ROOT / "docs" / "dev" / "phase-implementation-plan" / "06-analytics.md"
)


def _extract_symbol_name(raw_symbol: str) -> str:
    """Extract a searchable symbol from a requirement target cell.

    Args:
        raw_symbol: Raw symbol text from the markdown traceability table.

    Returns:
        Symbol name suitable for source lookup.
    """
    symbol = raw_symbol.strip().strip("`")
    symbol = symbol.split(":", 1)[0]
    symbol = symbol.split(" ", 1)[0]
    symbol = symbol.split("(", 1)[0]
    return symbol


def validate_requirement_matrix() -> list[tuple[str, str, str]]:
    """Validate every analytics requirement maps to an implementation anchor.

    Returns:
        Parsed requirement rows as ``(requirement_id, path, symbol)`` tuples.
    """
    rows: list[tuple[str, str, str]] = []
    table_line_pattern = re.compile(r"^\| ANL-")
    for line in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
        if not table_line_pattern.match(line):
            continue
        parts = [part.strip().strip("`") for part in line.strip().strip("|").split("|")]
        if len(parts) < 6:
            continue
        requirement_id, _group, _classification, _description, path_text, symbol = (
            parts[:6]
        )
        source_path = PROJECT_ROOT / path_text
        assert source_path.exists(), f"{requirement_id} missing path {path_text}"
        source_text = source_path.read_text(encoding="utf-8", errors="replace")
        symbol_name = _extract_symbol_name(symbol)
        if symbol_name:
            assert symbol_name in source_text, (
                f"{requirement_id} missing symbol {symbol_name} in {path_text}"
            )
        rows.append((requirement_id, path_text, symbol_name))
    return rows


def test_all_analytics_requirements_have_traceable_implementation() -> None:
    """Verify all explicit analytics requirements map to code, docs, or tests."""
    rows = validate_requirement_matrix()

    requirement_ids = {requirement_id for requirement_id, _path, _symbol in rows}
    assert len(rows) == 454
    assert len(requirement_ids) == 454
    assert "ANL-NFR-001" in requirement_ids
    assert "ANL-NFR-452" in requirement_ids
    assert "ANL-BR-001" in requirement_ids
    assert "ANL-BR-002" in requirement_ids
