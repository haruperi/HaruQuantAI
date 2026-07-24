"""Research Edge Lab workflow tests."""

from pathlib import Path

import pytest
from app.services.research import ResearchReport, run_edge_lab_profile
from app.utils import ValidationError
from tests.research._support import make_dataset, make_edge_lab_config


def test_edge_lab_returns_explicit_hypothesis_and_has_no_io(tmp_path: Path) -> None:
    """Verify selected deterministic stages produce advisory report evidence."""
    dataset = make_dataset()
    config = make_edge_lab_config(tmp_path)

    report = run_edge_lab_profile(
        dataset,
        hypothesis="Returns persist over one research bar.",
        config=config,
    )

    assert isinstance(report, ResearchReport)
    assert report.hypothesis == "Returns persist over one research bar."
    assert report.advisory_only is True
    assert report.evidence["selected_stages"] == ["data"]
    assert list(tmp_path.iterdir()) == []


def test_edge_lab_rejects_missing_hypothesis(tmp_path: Path) -> None:
    """Verify Research never invents a missing hypothesis."""
    with pytest.raises(ValidationError, match="INVALID_HYPOTHESIS"):
        run_edge_lab_profile(
            make_dataset(),
            hypothesis="",
            config=make_edge_lab_config(tmp_path),
        )


def test_edge_lab_fails_closed_for_unimplemented_stage(tmp_path: Path) -> None:
    """Verify unavailable selected stages are not silently skipped."""
    config = make_edge_lab_config(tmp_path, selected_stages=("data", "statistics"))

    with pytest.raises(ValidationError, match="UNAVAILABLE_SELECTED_STAGE"):
        run_edge_lab_profile(
            make_dataset(),
            hypothesis="A bounded hypothesis.",
            config=config,
        )
