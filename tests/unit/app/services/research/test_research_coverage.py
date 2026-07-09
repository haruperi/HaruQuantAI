# ruff: noqa: E501, D, ANN, S101
"""Coverage expansion tests for Research Service."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from app.services.research.data import (
    build_core_metric_profile,
    build_market_structure_profile,
    prepare_research_dataset,
    run_seasonality,
    validate_dataset,
)
from app.services.research.helpers import (
    calculate_adr,
    calculate_atr,
    calculate_correlation_matrix,
    calculate_returns,
    calculate_seasonality_statistics,
    calculate_session_statistics,
    calculate_spread_statistics,
    calculate_volatility,
    calmar_ratio,
    check_contradictory_evidence,
    check_hypothesis_testability,
    check_lookahead_bias_risk,
    expectancy,
    filter_events_by_symbol,
    max_drawdown,
    median_mae_mfe,
    parse_sentiment_snapshot,
    profit_factor,
    run_session_breakout_strategy,
    run_session_fade_strategy,
    sharpe_ratio,
    sortino_ratio,
    win_rate,
)
from app.services.research.reporting import (
    _safe_write,
    build_edge_lab_scorecard_report,
    generate_multi_symbol_report,
    save_json_report,
    save_markdown_report,
)
from app.services.research.studies.null_models import (
    compare_to_null,
    compute_null_percentile,
    get_acceptance_criteria,
    null_distribution_stats,
    r_space_null,
    random_entry_null,
    session_randomized_null,
    shuffle_returns_null,
)
from app.services.research.studies.structure import (
    build_market_structure_stability_report,
    build_metric_calibration_grid,
    build_research_evidence_pack,
    build_validation_summary,
    confidence_bucket,
    detect_swing_points,
    evaluate_metric_calibration_candidates,
    evaluate_profile_calibration,
    generate_research_hypothesis,
    label_realized_market_behavior,
    parse_news_items,
    resolve_market_structure_profile_overrides,
    symbol_class,
    timeframe_bucket,
)
from app.services.research.studies.unsupervised import (
    UnsupervisedResearchRequest,
    UnsupervisedResearchResult,
    adapt_signals_by_cluster,
    analyze_cluster_outperformance,
    build_unsupervised_insight_report,
    cluster_feature_space,
    compute_forward_returns,
    run_pca,
)
from app.utils.errors import ValidationError
from app.utils.settings import EdgeLabConfig, EdgeResult, EdgeStats


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Generate a clean sample OHLCV DataFrame for testing."""
    dates = pd.date_range(start="2026-01-01", periods=100, freq="h")
    np.random.seed(42)
    close_prices = 100.0 + np.cumsum(np.random.normal(0, 0.5, 100))
    df = pd.DataFrame(
        {
            "open": close_prices - 0.2,
            "high": close_prices + 0.5,
            "low": close_prices - 0.6,
            "close": close_prices,
            "volume": np.random.randint(100, 1000, 100).astype(float),
            "spread": np.random.uniform(1.0, 5.0, 100),
        },
        index=dates,
    )
    return df


# --- Helpers Tests ---
def test_parse_sentiment_snapshot() -> None:
    raw = [
        {
            "symbol": "EURUSD",
            "long_percentage": 60.0,
            "short_percentage": 40.0,
            "volume": 100.5,
        },
        {},
    ]
    parsed = parse_sentiment_snapshot(raw)
    assert len(parsed) == 2
    assert parsed[0]["symbol"] == "EURUSD"
    assert parsed[1]["long_percentage"] == 50.0


def test_filter_events_by_symbol() -> None:
    events = [
        {"currency": "EUR", "title": "EUR event"},
        {"currency": "USD", "title": "USD event"},
        {"currency": "GBP", "title": "GBP event"},
    ]
    filtered = filter_events_by_symbol(events, "EURUSD")
    assert len(filtered) == 2


def test_calculators() -> None:
    close = pd.Series([100.0, 101.0, 102.0])
    high = pd.Series([101.0, 102.0, 103.0])
    low = pd.Series([99.0, 100.0, 101.0])

    assert len(calculate_returns(close)) == 3
    assert len(calculate_volatility(calculate_returns(close), window=2)) == 3
    assert len(calculate_atr(high, low, close, window=2)) == 3
    assert len(calculate_adr(high, low, window=2)) == 3


def test_calculate_spread_statistics_empty() -> None:
    assert calculate_spread_statistics(pd.Series([], dtype=float)) == {
        "mean": 0.0,
        "std": 0.0,
        "max": 0.0,
        "min": 0.0,
    }


def test_calculate_session_statistics_empty() -> None:
    df = pd.DataFrame({"returns": []})
    assert calculate_session_statistics(df) == {
        "sample_size": 0,
        "mean": 0.0,
        "std": 0.0,
    }


def test_calculate_seasonality_statistics_empty() -> None:
    df = pd.DataFrame({"other": [1, 2]})
    assert calculate_seasonality_statistics(df) == {}


def test_calculate_correlation_matrix() -> None:
    df1 = pd.DataFrame({"close": [1.0, 1.1]})
    df2 = pd.DataFrame({"close": [2.0, 2.1]})
    corr = calculate_correlation_matrix([df1, df2])
    assert corr.shape == (2, 2)


def test_hypothesis_checks() -> None:
    df = pd.DataFrame({"returns": [-0.01, -0.02, 0.01]})
    assert check_lookahead_bias_risk(df) is False
    assert check_hypothesis_testability(df) is False
    assert check_contradictory_evidence(df) is True


def test_advisory_strategies() -> None:
    df = pd.DataFrame({"close": [1.0, 1.1]})
    assert "win_rate" in run_session_breakout_strategy(df)
    assert "win_rate" in run_session_fade_strategy(df)


def test_performance_indicators() -> None:
    assert calmar_ratio(10.0, 0.0) == 0.0
    assert calmar_ratio(10.0, 2.0) == 5.0

    assert expectancy(0.5, 10.0, -5.0) == 2.5

    assert max_drawdown(pd.Series([], dtype=float)) == 0.0
    assert max_drawdown(pd.Series([100.0, 95.0, 105.0])) == -0.05

    trades = [{"mae": 1.0, "mfe": 2.0}]
    assert median_mae_mfe(trades) == {"median_mae": 1.0, "median_mfe": 2.0}
    assert median_mae_mfe([]) == {"median_mae": 0.0, "median_mfe": 0.0}

    assert profit_factor([]) == 1.0
    assert profit_factor([{"r_multiple": 2.0}]) == float("inf")
    assert profit_factor([{"r_multiple": 2.0}, {"r_multiple": -1.0}]) == 2.0

    assert sharpe_ratio(pd.Series([], dtype=float)) == 0.0
    assert sharpe_ratio(pd.Series([0.01, 0.01])) == 0.0  # std is 0

    assert sortino_ratio(pd.Series([], dtype=float)) == 0.0
    assert sortino_ratio(pd.Series([0.01, 0.01])) == 0.0  # downside std is 0

    assert win_rate([]) == 0.0


# --- Data Prep Tests ---
def test_validate_dataset_warnings() -> None:
    # Inconsistent high
    df = pd.DataFrame(
        {"open": [1.10], "high": [1.05], "low": [1.00], "close": [1.08]},
        index=pd.date_range("2026-01-01", periods=1),
    )
    report = validate_dataset(df)
    assert any(i.code == "WARN_INCONSISTENT_HIGH" for i in report.issues)

    # Inconsistent low
    df2 = pd.DataFrame(
        {"open": [1.10], "high": [1.20], "low": [1.15], "close": [1.18]},
        index=pd.date_range("2026-01-01", periods=1),
    )
    report2 = validate_dataset(df2)
    assert any(i.code == "WARN_INCONSISTENT_LOW" for i in report2.issues)

    # Negative volume/spread
    df3 = pd.DataFrame(
        {
            "open": [1.10],
            "high": [1.20],
            "low": [1.00],
            "close": [1.15],
            "volume": [-100.0],
            "spread": [-1.0],
        },
        index=pd.date_range("2026-01-01", periods=1),
    )
    report3 = validate_dataset(df3)
    assert any(i.code == "WARN_NEGATIVE_VOLUME" for i in report3.issues)
    assert any(i.code == "WARN_NEGATIVE_SPREAD" for i in report3.issues)


def test_prepare_research_dataset_branches() -> None:
    dates = pd.date_range("2026-01-01", periods=5, tz="UTC")
    df = pd.DataFrame(
        {
            "open": [1.0, 1.1, np.nan, 1.2, 1.3],
            "high": [1.05, 1.15, np.nan, 1.25, 1.35],
            "low": [0.95, 1.05, np.nan, 1.15, 1.25],
            "close": [1.01, 1.11, np.nan, 1.21, 1.31],
            "spread": [1.0, 2.0, np.nan, 105.0, 1.5],
        },
        index=dates,
    )

    # timezone convert, drop na, cap spread
    config = EdgeLabConfig()
    config.cleaning_config.timezone = "America/New_York"
    config.cleaning_config.missing_bar_strategy = "drop"
    config.cleaning_config.spread_anomaly_threshold = 10.0

    ds = prepare_research_dataset(df, config)
    assert len(ds.data) == 4
    assert ds.data["spread"].max() == 10.0
    assert str(ds.data.index.tz) == "America/New_York"

    # forward fill missing bars
    config2 = EdgeLabConfig()
    config2.cleaning_config.missing_bar_strategy = "forward_fill"
    ds2 = prepare_research_dataset(df, config2)
    assert len(ds2.data) == 5
    assert not ds2.data["close"].isna().any()

    # interpolate missing bars
    config3 = EdgeLabConfig()
    config3.cleaning_config.missing_bar_strategy = "interpolate"
    ds3 = prepare_research_dataset(df, config3)
    assert len(ds3.data) == 5


def test_build_profiles(sample_ohlcv_data: pd.DataFrame) -> None:
    ds = prepare_research_dataset(sample_ohlcv_data)
    profile = build_core_metric_profile(ds)
    assert profile.metrics is not None

    m_profile = build_market_structure_profile(ds)
    assert m_profile.regime == "trending"

    season = run_seasonality(ds.data)
    assert season != {}


# --- Unsupervised Tests ---
def test_unsupervised_models() -> None:
    req = UnsupervisedResearchRequest(feature_columns=["f1"])
    assert req.n_components == 2

    res = UnsupervisedResearchResult(
        pca_explained_variance=[0.5, 0.3], cluster_centers=[[1.0]], seed=42
    )
    assert len(res.pca_explained_variance) == 2


def test_unsupervised_unsupported_data() -> None:
    df = pd.DataFrame({"f1": [1.0]})
    # Too few rows for n_components=2
    with pytest.raises(ValidationError):
        run_pca(df, n_components=2)
    with pytest.raises(ValidationError):
        cluster_feature_space(df, n_clusters=3)


def test_compute_forward_returns() -> None:
    close = pd.Series([1.0, 1.1, 1.2])
    with pytest.raises(ValidationError):
        compute_forward_returns(close, horizon=0)
    ret = compute_forward_returns(close, horizon=1)
    assert len(ret) == 3


def test_analyze_cluster_outperformance() -> None:
    df = pd.DataFrame({"research_forward_returns": [0.0005, -0.0005, 0.0]})
    labels = [0, 1, 2]
    with pytest.raises(ValidationError):
        analyze_cluster_outperformance(df, labels, "missing_col")

    res = analyze_cluster_outperformance(df, labels)
    assert res[0]["regime_name"] == "High Growth"
    assert res[1]["regime_name"] == "Contraction"
    assert res[2]["regime_name"] == "Sideways Stable"


def test_adapt_signals_by_cluster() -> None:
    perf = {0: {"mean_forward_return": -0.0005}, 1: {"mean_forward_return": 0.0005}}
    rec = adapt_signals_by_cluster(perf)
    assert rec["recommendations"]["0"]["action"] == "reduce_exposure_advisory"
    assert rec["recommendations"]["1"]["action"] == "maintain_exposure_advisory"


def test_build_unsupervised_insight_report() -> None:
    report = build_unsupervised_insight_report("EURUSD", "H1", {}, {})
    assert report["symbol"] == "EURUSD"


# --- Null Models Tests ---
def test_null_models_coverage() -> None:
    assert compute_null_percentile(1.0, []) == 50.0
    assert compute_null_percentile(1.5, [1.0, 2.0]) == 50.0

    cmp = compare_to_null(1.5, [1.0, 2.0])
    assert cmp["observed"] == 1.5

    crit = get_acceptance_criteria([1.0, 2.0, 3.0])
    assert "critical_value_high" in crit

    df_empty = pd.DataFrame({"returns": []})
    assert len(random_entry_null(df_empty)) == 1000

    df_short = pd.DataFrame({"returns": [1.0]})
    assert len(random_entry_null(df_short, horizon=5)) == 1000

    assert len(r_space_null()) == 1000

    assert len(session_randomized_null(df_empty)) == 500

    assert len(shuffle_returns_null(df_empty)) == 500

    stats = null_distribution_stats([])
    assert stats == {"mean": 0.0, "std": 0.0}


# --- Structure Studies Tests ---
def test_structure_studies_coverage(sample_ohlcv_data: pd.DataFrame) -> None:
    # Small length
    swings = detect_swing_points(sample_ohlcv_data.iloc[:5])
    assert len(swings) == 0

    grid = build_metric_calibration_grid(["sharpe"], [1.5])
    evaluated = evaluate_metric_calibration_candidates(sample_ohlcv_data, grid)
    assert len(evaluated) == 1

    profile = resolve_market_structure_profile_overrides("EURUSD", "H1", "major")
    assert evaluate_profile_calibration(profile, sample_ohlcv_data) == 0.9

    assert timeframe_bucket("M5") == "scalping"
    assert timeframe_bucket("D1") == "positional"

    assert symbol_class("GBPUSD") == "major"
    assert symbol_class("GBPJPY") == "cross"

    assert confidence_bucket(0.9) == "high"
    assert confidence_bucket(0.6) == "medium"
    assert confidence_bucket(0.3) == "low"

    assert label_realized_market_behavior(pd.DataFrame({"close": []})) == "mixed"
    assert (
        label_realized_market_behavior(pd.DataFrame({"close": [1.0, 1.1]})) == "trend"
    )
    assert (
        label_realized_market_behavior(pd.DataFrame({"close": [1.0, 1.00001]}))
        == "reversion"
    )

    assert build_validation_summary(sample_ohlcv_data)["rows_count"] == 100
    assert (
        build_market_structure_stability_report(sample_ohlcv_data)["stability_index"]
        == 0.85
    )

    news = [{"headline": "headline", "timestamp": "time"}]
    assert parse_news_items(news)[0]["headline"] == "headline"

    hyp = generate_research_hypothesis("desc", ["ev"])
    assert hyp["hypothesis"] == "desc"

    pack = build_research_evidence_pack("EURUSD", "H1", {}, {})
    assert pack["symbol"] == "EURUSD"


# --- Reporting Tests ---
def test_reporting_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="Directory traversal detected"):
        _safe_write("content", "../traversal.txt", overwrite=True)

    file_path = tmp_path / "existing.txt"
    file_path.write_text("old", encoding="utf-8")

    # Overwrite False
    res = _safe_write("new", str(file_path), overwrite=False)
    assert res is False
    assert file_path.read_text(encoding="utf-8") == "old"


def test_reporting_helpers() -> None:
    md = generate_multi_symbol_report([])
    assert "Multi-Symbol" in md

    res = save_json_report({}, "report_test.json")
    assert res is True
    Path("report_test.json").unlink()

    res_md = save_markdown_report({}, "report_test.md")
    assert res_md is True
    Path("report_test.md").unlink()

    config = EdgeLabConfig()
    stats = EdgeStats(
        sample_size=10,
        win_rate=0.5,
        profit_factor=1.5,
        expectancy=0.5,
        sharpe_ratio=1.0,
    )
    result = EdgeResult(study_name="test_study", config=config, stats=stats)
    card = build_edge_lab_scorecard_report("EURUSD", "H1", [result])
    assert card["symbol"] == "EURUSD"
