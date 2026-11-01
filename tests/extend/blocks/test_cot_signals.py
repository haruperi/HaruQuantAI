"""Unit tests verifying all 54 COT specialized signals and external feed bindings."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from app.extend.blocks.registry import BlockRegistry
from app.extend.blocks.series import IndicatorSeries


@pytest.fixture(scope="module")
def cot_test_feeds() -> dict[str, IndicatorSeries]:
    """Generate aligned multi-year positioning series for COT testing."""
    n = 200
    hedg52 = IndicatorSeries(np.linspace(0.4, 0.8, n), name="Hedg52")
    spec52 = IndicatorSeries(np.linspace(0.6, 0.2, n), name="Spec52")
    hedg156 = IndicatorSeries(np.linspace(0.45, 0.75, n), name="Hedg156")
    spec156 = IndicatorSeries(np.linspace(0.55, 0.25, n), name="Spec156")
    small52 = IndicatorSeries(np.linspace(0.5, 0.3, n), name="Small52")
    score = IndicatorSeries(np.linspace(-0.2, 0.6, n), name="COTScore")
    series = IndicatorSeries(np.linspace(0.1, 0.9, n), name="COTSeries")

    return {
        "cot_hedg": hedg52,
        "cot_spec": spec52,
        "cot_small": small52,
        "cot_hedg52": hedg52,
        "cot_spec52": spec52,
        "cot_small52": small52,
        "cot_hedg156": hedg156,
        "cot_spec156": spec156,
        "cot_score": score,
        "cot_series": series,
    }


def test_all_cot_specialized_signals_resolve_and_execute(
    cot_test_feeds: dict[str, IndicatorSeries],
) -> None:
    """Verify all 54 specialized signals bind correctly to external COT series."""
    registry = BlockRegistry()
    registry.discover("app/extend/blocks", authorized_root="app/extend")
    catalog = registry.snapshot()

    manifest_path = Path("app/extend/blocks/indicators/donor_compositions.json")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    cot_signals = [
        m
        for m in data["mappings"]
        if m.get("owner_id") == "indicator.volume.cot"
        and m.get("status") == "specialized_signal"
    ]
    assert len(cot_signals) == 54

    default_feed = cot_test_feeds["cot_hedg52"]

    for entry in cot_signals:
        sig_id = entry["id"]
        descriptor = catalog.require(sig_id)
        assert descriptor.spec.category == "indicator_signals"
        assert descriptor.spec.dependencies == ("indicator.volume.cot",)

        bindings = descriptor.input_bindings
        args: dict[str, IndicatorSeries] = {}
        for param_name, b_info in bindings.items():
            if b_info.get("kind") == "external":
                field_name = b_info["field"]
                args[param_name] = cot_test_feeds.get(field_name, default_feed)
            else:
                args[param_name] = default_feed

        target_fn = descriptor.instantiate()
        result = target_fn(**args)
        assert isinstance(result, (bool, float, int))
