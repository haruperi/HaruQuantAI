"""Golden package-root API coverage for the Data domain."""

from __future__ import annotations

from app.services import data

_EXPECTED_API = {
    "aggregate_ticks_to_bars",
    "align_multitimeframe_data",
    "clear_data_cache",
    "create_backup",
    "create_data_update_job",
    "describe_import_dialects",
    "enforce_retention_policy",
    "generate_synthetic_bars",
    "generate_synthetic_ticks",
    "generate_tick_series",
    "generate_tick_series_to_parquet",
    "get_data_availability",
    "get_data_update_job_status",
    "get_feed_status",
    "get_historical_volume",
    "get_market_data",
    "get_market_hours",
    "get_quality_policy",
    "get_spread_data",
    "get_symbol_metadata",
    "get_tick_data",
    "get_trading_sessions",
    "import_external_dataset",
    "inspect_data_quality",
    "list_symbols",
    "load_local_dataset",
    "resample_ohlcv",
    "restore_from_backup",
    "run_data_update_job_once",
    "save_market_data",
    "start_data_update_job",
    "stop_data_update_job",
    "summarize_quality_remediation",
    "to_ohlcv_dataframe",
    "to_tick_dataframe",
}


def test_package_root_exports_exact_approved_surface() -> None:
    """No undeclared alias or missing operation crosses the package root."""
    assert set(data.__all__) == _EXPECTED_API
    assert {name for name in _EXPECTED_API if hasattr(data, name)} == _EXPECTED_API
