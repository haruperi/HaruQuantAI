"""Complete in-memory Edge Lab integration evidence."""

from collections.abc import Mapping
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from app.services.research import (
    create_research_value,
    is_research_value,
    run_edge_lab_profile,
)
from tests.research._support import make_dataset, make_edge_lab_config


def _full_dataset() -> object:
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


def _study_config() -> object:
    """Build complete bounded settings for all three study families."""
    common = {
        "hold_bars": 1,
        "side": "buy",
        "minimum_samples": 1,
        "q": 0.1,
        "null_quantile": 0.9,
    }
    return create_research_value(
        "StudyConfig",
        mean_reversion={**common, "lookback": 2, "entry_zscore": 0.5},
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
    """FR-RES-096 composes every selected deterministic stage."""
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
    response = run_edge_lab_profile(
        _full_dataset(),
        hypothesis="A complete bounded Edge Lab hypothesis.",
        config=config,
    )
    assert response.status == "success"
    report = response.data
    assert is_research_value(report, "ResearchReport")
    assert report.evidence["selected_stages"] == list(selected)
    assert set(report.evidence) >= set(selected)
    leakage = report.evidence["leakage"]
    profiles = report.evidence["profiles"]
    assert isinstance(leakage, Mapping)
    assert isinstance(profiles, Mapping)
    assert leakage["severity"] != "high"
    assert profiles["advisory_only"] is True
    assert list(tmp_path.iterdir()) == []
