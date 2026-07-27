"""Research Edge Lab workflow tests."""

from collections.abc import Mapping
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data import MarketDataset
from app.services.research import ResearchReport, run_edge_lab_profile
from app.services.research.contracts import StudyConfig
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


def test_edge_lab_rejects_studies_without_safe_feature_stages(
    tmp_path: Path,
) -> None:
    """Verify selected study orchestration requires leakage-reviewed features."""
    config = make_edge_lab_config(tmp_path, selected_stages=("data", "studies"))

    with pytest.raises(ValidationError, match="STUDIES_REQUIRE_SAFE_FEATURES"):
        run_edge_lab_profile(
            make_dataset(),
            hypothesis="A bounded hypothesis.",
            config=config,
        )


def _full_dataset() -> MarketDataset:
    """Build a sixty-row variant of the canonical bounded dataset."""
    dataset = make_dataset()
    first = dataset.records[0]
    records = tuple(
        first.model_copy(
            update={
                "timestamp": first.timestamp + timedelta(minutes=index),
                "available_at": first.available_at + timedelta(minutes=index),
                "close": first.close + Decimal(index) / Decimal(100),
            }
        )
        for index in range(60)
    )
    return dataset.model_copy(
        update={
            "records": records,
            "start": records[0].timestamp,
            "end": records[-1].timestamp,
            "available_at": records[-1].available_at,
            "record_count": len(records),
        }
    )


def _study_config() -> StudyConfig:
    """Build complete bounded settings for all three study families."""
    common = {
        "hold_bars": 1,
        "side": "buy",
        "minimum_samples": 1,
        "q": 0.1,
        "null_quantile": 0.9,
    }
    return StudyConfig(
        mean_reversion={
            **common,
            "lookback": 2,
            "entry_zscore": 0.5,
        },
        trend_persistence={
            **common,
            "lookback": 2,
            "minimum_move": 0.0001,
        },
        session={
            "horizon": 1,
            "minimum_samples": 1,
            "q": 0.1,
            "null_quantile": 0.9,
        },
    )


def test_edge_lab_executes_every_configured_stage(tmp_path: Path) -> None:
    """Verify FR-RES-096 composes every selected deterministic stage."""
    selected = (
        "profiles",
        "modeling",
        "market_structure",
        "seasonality",
        "studies",
        "statistics",
        "metrics",
        "leakage",
        "features",
        "data",
    )
    config = replace(
        make_edge_lab_config(tmp_path, selected_stages=selected),
        studies=_study_config(),
    )

    report = run_edge_lab_profile(
        _full_dataset(),
        hypothesis="A complete bounded Edge Lab hypothesis.",
        config=config,
    )

    assert report.advisory_only is True
    assert report.evidence["selected_stages"] == list(selected)
    assert set(report.evidence) >= set(selected)
    leakage = report.evidence["leakage"]
    profiles = report.evidence["profiles"]
    assert isinstance(leakage, Mapping)
    assert isinstance(profiles, Mapping)
    assert leakage["severity"] != "high"
    assert profiles["advisory_only"] is True
    assert list(tmp_path.iterdir()) == []
