"""Deterministic integration workflow boundary evidence for WF-INDI-006 and WF-INDI-007.

Exercises stage inputs and outputs through public domain functions using
deterministic fixtures without external sockets or MT5 dependency.
"""

from __future__ import annotations

from app.services.indicators import (
    build_indicator_config,
    cmf,
    doji,
    engulfing,
    get_capability_matrix,
    get_indicator,
    get_indicator_result_metadata,
    get_indicator_result_values,
    get_warmup_requirement,
    inside_bar,
    mfi,
    obv,
    pinbar,
    price_volume_distribution,
    validate_indicator,
)

from tests.indicators.helpers import build_dataset, unwrap_response


def test_wf_indi_006_candlestick_boundary_flow() -> None:
    """WF-INDI-006: Candlestick pattern detection workflow boundary test."""
    dataset = build_dataset(
        [
            (1.0, 1.5, 0.5, 1.05, 100.0),
            (1.0, 1.8, 0.8, 1.7, 120.0),
            (1.5, 1.6, 1.4, 1.55, 90.0),
            (1.2, 1.7, 0.6, 1.65, 110.0),
        ]
    )

    # Stage 1: Spec & capability inspection
    spec = unwrap_response(get_indicator("engulfing"))
    assert spec.indicator_id == "engulfing"

    # Stage 2: Validation & Warmup requirement
    config = build_indicator_config(
        "engulfing", source=None, formula_version=spec.formula_version
    )
    validated = unwrap_response(validate_indicator("engulfing", dataset, config))
    assert validated.indicator_id == "engulfing"

    warmup = unwrap_response(get_warmup_requirement("engulfing", config))
    assert warmup.minimum_observations >= 2

    # Stage 3: Calculation of detectors
    doji_res = unwrap_response(doji(dataset, threshold=0.1))
    engulfing_res = unwrap_response(engulfing(dataset))
    pinbar_res = unwrap_response(pinbar(dataset))
    inside_bar_res = unwrap_response(inside_bar(dataset))

    for res in (doji_res, engulfing_res, pinbar_res, inside_bar_res):
        values = get_indicator_result_values(res)
        meta = get_indicator_result_metadata(res)
        assert meta["schema_id"] == "indicators.indicator_series.v1"
        assert len(values) == dataset.record_count


def test_wf_indi_007_volume_distribution_boundary_flow() -> None:
    """WF-INDI-007: Volume distribution and flow workflow boundary test."""
    dataset = build_dataset(
        [
            (10.0, 12.0, 9.0, 11.0, 500.0),
            (11.0, 13.0, 10.5, 12.5, 600.0),
            (12.5, 14.0, 11.5, 12.0, 450.0),
            (12.0, 12.5, 10.0, 10.5, 700.0),
        ]
    )

    # Stage 1: Introspection & validation
    matrix = unwrap_response(get_capability_matrix())
    assert len(matrix) == 64

    # Stage 2: Volume-flow calculations
    cmf_res = unwrap_response(cmf(dataset, period=2))
    obv_res = unwrap_response(obv(dataset))
    mfi_res = unwrap_response(mfi(dataset, period=2))
    pvd_res = unwrap_response(price_volume_distribution(dataset, period=2, bins=2))

    for res in (cmf_res, obv_res, mfi_res, pvd_res):
        values = get_indicator_result_values(res)
        meta = get_indicator_result_metadata(res)
        assert meta["schema_id"] == "indicators.indicator_series.v1"
        assert len(values) == dataset.record_count
