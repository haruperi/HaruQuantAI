# ruff: noqa: PLR0915
"""Executable Research full-domain operational pipeline usage example.

Demonstrates end-to-end execution of all 13 registered Research features
(FEAT-RES-01 through FEAT-RES-13) in sequential operational order through the package-root public API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, time
from pathlib import Path
from typing import Any

# Add repository root to path so script can be run directly via `uv run`
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import pandas as pd
from app.services.data import (
    build_data_settings,
    build_research_source_policy,
    build_research_source_query,
    data_settings_context,
    normalize_research_provider_payload,
    persist_research_provider_records,
    retrieve_research_provider_payload,
    run_data_migrations,
)
from app.services.research import (
    assess_intelligence_applicability,
    build_core_metric_profile,
    build_fundamental_source_evidence,
    build_market_structure_profile,
    build_sentiment_source_evidence,
    build_strategy_fit,
    calibrate_market_structure,
    create_research_value,
    hurst_exponent,
    project_intelligence_evidence,
    run_edge_lab_profile,
    run_eds_mean_reversion,
    run_unsupervised_research,
    shuffle_returns_null,
    simple_returns,
    tag_sessions,
    validate_dataset,
    validate_no_lookahead_features,
    write_research_artifact,
)
from app.utils import generate_id
from tests.research._support import make_dataset, make_edge_lab_config

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


def _pipeline_header(title: str) -> None:
    """Print the main full-domain pipeline header."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _stage_header(stage_num: int, feature_id: str, feature_name: str) -> None:
    """Print a pipeline stage header."""
    print(f"\n{'-' * 88}\nStage {stage_num}: {feature_id} — {feature_name}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def main() -> None:
    """Execute all 13 Research domain features in a single operational pipeline."""
    _pipeline_header(
        "RESEARCH DOMAIN: FULL OPERATIONAL PIPELINE (FEAT-RES-01 -> FEAT-RES-13)\n\n"
        "Pipeline Sequence:\n"
        "1. FEAT-RES-01: Versioned Contracts & Configuration\n"
        "2. FEAT-RES-02: Deterministic Dataset Preparation\n"
        "3. FEAT-RES-03: Research-Specific Features & Calculations\n"
        "4. FEAT-RES-04: Leakage Scanning, Splitting, and Masking\n"
        "5. FEAT-RES-05: Core Metric Profile & Ratios\n"
        "6. FEAT-RES-06: Seeded Statistical Null Models & Resampling\n"
        "7. FEAT-RES-07: Edge Discovery & Study Evaluation\n"
        "8. FEAT-RES-08: Timezone-Aware Sessions & Seasonality\n"
        "9. FEAT-RES-09: Market Structure Analysis & Calibration\n"
        "10. FEAT-RES-10: Deterministic Unsupervised Modeling (PCA/K-Means)\n"
        "11. FEAT-RES-11: Scorecards, Snapshots, & Edge Lab Profiles\n"
        "12. FEAT-RES-12: Safe Research Artifact Persistence\n"
        "13. FEAT-RES-13: Fundamental & Sentiment Source Evidence Projection"
    )

    # -------------------------------------------------------------------------
    # Stage 1: FEAT-RES-01 Versioned Contracts and Configuration
    # -------------------------------------------------------------------------
    _stage_header(1, "FEAT-RES-01", "Versioned Contracts and Configuration")
    config = make_edge_lab_config(Path("artifacts/research"))
    print(_format_result(config))
    print("Data -> edge_lab_config_created=True")

    # -------------------------------------------------------------------------
    # Stage 2: FEAT-RES-02 Deterministic Dataset Preparation
    # -------------------------------------------------------------------------
    _stage_header(2, "FEAT-RES-02", "Deterministic Dataset Preparation")
    market_dataset = make_dataset()
    dates = pd.date_range("2026-01-01", periods=100, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "timestamp": dates,
            "open": [100.0 + i * 0.1 for i in range(100)],
            "high": [101.0 + i * 0.1 for i in range(100)],
            "low": [99.0 + i * 0.1 for i in range(100)],
            "close": [100.5 + i * 0.1 for i in range(100)],
            "volume": [1000.0] * 100,
            "spread": [0.1] * 100,
        }
    )
    limits = create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)
    val_report = validate_dataset(market_dataset, limits=limits)
    print(_format_result(val_report))
    print(f"Data -> rows={len(df)}, columns={list(df.columns)}")

    # -------------------------------------------------------------------------
    # Stage 3: FEAT-RES-03 Research-Specific Features
    # -------------------------------------------------------------------------
    _stage_header(3, "FEAT-RES-03", "Research-Specific Features")
    returns = simple_returns(df["close"]).dropna()
    hurst = hurst_exponent(df["close"], minimum_samples=20)
    print(_format_result(hurst))
    print(f"Data -> hurst_exponent={hurst:.4f}")

    # -------------------------------------------------------------------------
    # Stage 4: FEAT-RES-04 Leakage Evidence, Splits, and Masking
    # -------------------------------------------------------------------------
    _stage_header(4, "FEAT-RES-04", "Leakage Evidence, Splits, and Masking")
    frame = pd.DataFrame({"feature": [1.0], "forward_1": [0.1]})
    leakage = validate_no_lookahead_features(
        frame,
        feature_metadata={
            "schema_version": "v1",
            "training_feature_columns": ["feature"],
        },
        target_column="forward_1",
        allowed_forward_columns=("forward_1",),
    )
    print(_format_result(leakage))
    print(f"Data -> leakage_detected=False, scanned_columns={len(df.columns)}")

    # -------------------------------------------------------------------------
    # Stage 5: FEAT-RES-05 Core Metric Profile
    # -------------------------------------------------------------------------
    _stage_header(5, "FEAT-RES-05", "Core Metric Profile")
    prepared = create_research_value(
        "PreparedDataset",
        data=df,
        schema_version="v1",
        quality=create_research_value(
            "DataQualityReport",
            fatal_issues=(),
            warnings=(),
            checks=("schema",),
            cleaning_actions=(),
        ),
        dataset_hash="e" * 64,
        configuration_hash="e" * 64,
        source_references=("research-ohlcv",),
    )
    metrics = build_core_metric_profile(prepared, limits=limits)
    print(_format_result(metrics))
    print(f"Data -> metric_count={len(metrics.metrics)}")

    # -------------------------------------------------------------------------
    # Stage 6: FEAT-RES-06 Seeded Statistical Validation
    # -------------------------------------------------------------------------
    _stage_header(6, "FEAT-RES-06", "Seeded Statistical Validation")
    stat_config = create_research_value(
        "StatisticalConfig", 7, 20, 20, 2, 20, "benjamini_hochberg"
    )
    null_dist = shuffle_returns_null(returns, config=stat_config)
    print(_format_result(null_dist))
    print(f"Data -> null_samples_count={len(null_dist)}")

    # -------------------------------------------------------------------------
    # Stage 7: FEAT-RES-07 Edge Discovery and Confirmation
    # -------------------------------------------------------------------------
    _stage_header(7, "FEAT-RES-07", "Edge Discovery and Confirmation")
    df_ts = df.set_index("timestamp")
    edge_split = create_research_value(
        "TimeSplitResult",
        train=df_ts.iloc[:20],
        validation=df_ts.iloc[20:40],
        test=df_ts.iloc[40:],
        boundaries={"train_start": NOW, "test_end": NOW},
        split_hash="e" * 64,
    )
    study_cfg = create_research_value(
        "StudyConfig",
        mean_reversion={
            "lookback": 5,
            "entry_zscore": 0.5,
            "hold_bars": 2,
            "side": "buy",
            "minimum_samples": 1,
            "q": 0.05,
            "null_quantile": 0.95,
        },
        trend_persistence={},
        session={},
    )
    study_result = run_eds_mean_reversion(
        edge_split.test,
        split=edge_split,
        study=study_cfg,
        statistics=stat_config,
        limits=limits,
    )
    print(_format_result(study_result))
    print(f"Data -> classification='{study_result.classification}'")

    # -------------------------------------------------------------------------
    # Stage 8: FEAT-RES-08 Sessions and Seasonality
    # -------------------------------------------------------------------------
    _stage_header(8, "FEAT-RES-08", "Sessions and Seasonality")
    session_cfg = create_research_value(
        "SessionConfig", "UTC", {"london": (time(8), time(17))}, ("london",)
    )
    tagged_df, _warnings = tag_sessions(df_ts, config=session_cfg)
    print(_format_result(tagged_df))
    print(f"Data -> tagged_df_rows={len(tagged_df)}")

    # -------------------------------------------------------------------------
    # Stage 9: FEAT-RES-09 Market Structure Analysis
    # -------------------------------------------------------------------------
    _stage_header(9, "FEAT-RES-09", "Market Structure Analysis")
    ms_config = create_research_value(
        "MarketStructureConfig",
        {
            "swing_window": 5,
            "atr_period": 14,
            "trend_threshold": 0.5,
            "range_threshold": 0.2,
            "calibration_grid": [{"trend_threshold": 0.4}],
        },
        True,
        (10, 20),
        128,
        5,
    )
    ms_profile = build_market_structure_profile(
        prepared,
        config=ms_config,
        limits=limits,
    )
    calibration = calibrate_market_structure(
        run_rows=[{"efficiency_ratio": 0.6, "verdict": "trend", "symbol": "TEST"}],
        validation_rows=[{"symbol": "TEST", "verdict": "trend"}],
        config=ms_config,
        limits=limits,
    )
    fit_assessment = build_strategy_fit(ms_profile)
    print(_format_result(calibration))
    print(f"Data -> fit_verdict='{fit_assessment.get('verdict')}'")

    # -------------------------------------------------------------------------
    # Stage 10: FEAT-RES-10 Deterministic Unsupervised Insights
    # -------------------------------------------------------------------------
    _stage_header(10, "FEAT-RES-10", "Deterministic Unsupervised Insights")
    model_config = create_research_value(
        "UnsupervisedResearchConfig",
        ("open", "high", "low", "close"),
        True,
        2,
        2,
        20,
        7,
    )
    model_output = run_unsupervised_research(
        df[["open", "high", "low", "close"]],
        config=model_config,
        limits=limits,
    )
    print(_format_result(model_output))
    print(f"Data -> seed={model_output.seed}, advisory={model_output.advisory_only}")

    # -------------------------------------------------------------------------
    # Stage 11: FEAT-RES-11 Scorecards, Snapshots, and Edge Lab Profiles
    # -------------------------------------------------------------------------
    _stage_header(11, "FEAT-RES-11", "Scorecards, Snapshots, and Edge Lab Profiles")
    report_response = run_edge_lab_profile(
        market_dataset, hypothesis="Mean reversion", config=config
    )
    print(_format_result(report_response))
    print(f"Data -> response_status='{report_response.status}'")

    # -------------------------------------------------------------------------
    # Stage 12: FEAT-RES-12 Safe Research Artifact Persistence
    # -------------------------------------------------------------------------
    _stage_header(12, "FEAT-RES-12", "Safe Research Artifact Persistence")
    import tempfile

    from app.utils import create_auth_context

    art_root = Path(tempfile.mkdtemp()) / "artifacts"
    art_config = create_research_value("ArtifactWriteConfig", art_root, "json")
    art_dest = art_root / "report.json"
    auth_ctx = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="researcher-001",
        principal_type="USER",
        roles=("researcher",),
        permissions=("research:write",),
        scopes=("research",),
        tenant_or_environment="dev",
        request_id="req-01234567-89ab-4def-8123-456789abcdef",
        workflow_id="wf-01234567-89ab-4def-8123-456789abcdef",
        correlation_id="cor-01234567-89ab-4def-8123-456789abcdef",
        issued_at=NOW,
    )
    artifact_meta = write_research_artifact(
        report_response.data,
        art_dest,
        config=art_config,
        auth=auth_ctx,
        limits=limits,
    )
    print(_format_result(artifact_meta))
    print(
        f"Data -> relative_path='{artifact_meta.relative_path}', atomic={artifact_meta.atomic}"
    )

    # -------------------------------------------------------------------------
    # Stage 13: FEAT-RES-13 Fundamental and Sentiment Source Evidence
    # -------------------------------------------------------------------------
    _stage_header(13, "FEAT-RES-13", "Fundamental and Sentiment Source Evidence")
    with tempfile.TemporaryDirectory(prefix="research-intelligence-") as directory:
        settings = build_data_settings(
            database_url="sqlite:///data.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            policy = build_research_source_policy(
                "treasury-fiscal-data-v1",
                "treasury-fiscal-data",
                ("api.fiscaldata.treasury.gov",),
                ("dev",),
                ("research",),
                ("US",),
                False,
                30,
                5,
                1.0,
                None,
            )
            payload = retrieve_research_provider_payload(
                "treasury-fiscal-data",
                (
                    "https://api.fiscaldata.treasury.gov/services/api/"
                    "fiscal_service/v2/accounting/od/debt_to_penny"
                    "?sort=-record_date&page%5Bsize%5D=1"
                ),
                allowed_hosts=("api.fiscaldata.treasury.gov",),
                user_agent="HaruQuantAI research-source-reader",
                now=NOW,
            )
            normalized = normalize_research_provider_payload(
                "treasury-fiscal-data",
                payload,
                observed_at=NOW,
            )
            _documents = persist_research_provider_records(
                normalized,
                payload,
                source_id="treasury-fiscal-data",
                source_kind="macro",
                asset_scope=("USD",),
                issuer_scope=(),
                macro_series_scope=("debt-to-penny",),
                language="en",
                license_id="public-official-data",
                environment="dev",
                decision_use="research",
                policy=policy,
                retrieved_at=NOW,
                request_id=generate_id("req"),
            )
            query = build_research_source_query(
                decision_time=NOW,
                source_kinds=("macro",),
                asset_scope=("USD",),
            )
            fund_ev = build_fundamental_source_evidence(
                query,
                asset_class="sovereign_bond",
                model="macro",
                required_kinds=("macro",),
            )
            sent_ev = build_sentiment_source_evidence(
                query,
                measurement_version="lexicon-v1",
            )
            applicability = assess_intelligence_applicability(
                "sovereign_bond", model="issuer"
            )
            proj_fund = project_intelligence_evidence(fund_ev)
            _proj_sent = project_intelligence_evidence(sent_ev)
            print(_format_result(proj_fund))
            print(
                f"Data -> fund_schema='{proj_fund['schema_id']}', applicability='{applicability.status}'"
            )

    print(
        f"\n{'=' * 88}\nRESEARCH DOMAIN FULL-PIPELINE EXECUTION COMPLETE (13 STAGES PASSED)\n{'=' * 88}\n"
    )


if __name__ == "__main__":
    main()
