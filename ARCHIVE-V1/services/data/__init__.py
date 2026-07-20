"""Expose data service classes and function tools without implementing them.

Purpose:
    Re-export every public class and function implemented across the data
    service modules so callers can import them from ``app.services.data``.

Notes:
    Eight public names are defined in two modules each. To avoid shadowing, the
    tool-layer binding wins at this package level (``market_tools``/``csv``);
    the duplicate definitions in ``calendar``, ``gateway``, ``storage``, and
    ``transforms`` remain reachable through their own submodules.
"""

from app.services.utils.standard import standardize_domain_exports

# csv.py
from .csv import (
    CSVDataSource,
    clear_data_cache,
    csv_data_fetch_range,
    csv_data_load,
    csv_data_saver_file_exists,
    csv_data_saver_load,
    csv_data_saver_save,
    get_cached_data,
    load_csv,
)

# frames.py
from .frames import Data

# gateway.py (get_symbol_metadata / get_data_availability bind to market_tools)
from .gateway import (
    BrokerAdapter,
    CSVAdapter,
    ParquetAdapter,
    SourceAdapterProtocol,
    SyntheticAdapter,
    TokenBucketLimiter,
    check_rate_limit,
    get_circuit_breaker,
    update_circuit_breaker,
    normalize_file_records,
    check_circuit_breaker_barrier,
    get_source_adapter,
    execute_gateway_request,
    get_data,
    get_symbol_metadata,
    list_symbols,
    get_data_availability,
)

# generators.py
from .generators import (
    SPREAD_FIXED,
    SPREAD_NATIVE,
    SPREAD_VARIABLE,
    SUPPORTED_MODELS,
    SUPPORTED_SPREAD_MODELS,
    TICK_MODEL_GENERATED,
    TICK_MODEL_OHLC_M1,
    TICK_MODEL_REAL,
    TICK_MODEL_TRADING_BAR,
    TicksGenerator,
    generate_ticks,
    generate_ticks_to_parquet,
)

# labeling.py
from .labeling import labeler_lexlb

# licensing.py
from .licensing import register_license, validate_license

# models.py
from .models import (
    DataAvailability,
    OHLCVRecord,
    SpreadRecord,
    SymbolMetadata,
    TickRecord,
    validate_utc_timestamp_helper,
)

# parquet.py
from .parquet import (
    get_data_dir,
    load_parquet,
    parquet_data_load,
    parquet_data_saver_file_exists,
    parquet_data_saver_load,
    parquet_data_saver_save,
)

# scheduler.py
from .scheduler import (
    create_data_update_job,
    get_data_update_job_status,
    get_feed_status,
    handle_feed_overflow,
    recover_crashed_jobs,
    register_mock_feed,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)

# storage.py (clear_data_cache / get_cached_data bind to csv)
from .storage import (
    DatabaseHelper,
    generate_cache_key,
    load_local_dataset,
    load_ohlcv_csv,
    save_market_data,
    set_cached_data,
    validate_storage_path,
)

# transforms.py (resample_ohlcv / align_multitimeframe_data bind to market_tools)
from .transforms import (
    BarAggregator,
    TimeframeManager,
    aggregate_ticks_to_bars,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    label_market_data,
    timeframe_to_minutes,
    timeframe_to_pandas_freq,
    align_multitimeframe_data
)

# validation.py
from .validation import (
    normalize_numeric,
    validate_bars,
    validate_limit,
    validate_step_alignment,
    validate_timeframe,
    validate_timezone,
)

__all__ = [
    "BarAggregator",
    "BrokerAdapter",
    "CSVAdapter",
    "CSVDataSource",
    "Data",
    "DataAvailability",
    "DatabaseHelper",
    "OHLCVRecord",
    "ParquetAdapter",
    "SourceAdapterProtocol",
    "SpreadRecord",
    "SymbolMetadata",
    "SyntheticAdapter",
    "SPREAD_FIXED",
    "SPREAD_NATIVE",
    "SPREAD_VARIABLE",
    "SUPPORTED_MODELS",
    "SUPPORTED_SPREAD_MODELS",
    "TICK_MODEL_GENERATED",
    "TICK_MODEL_OHLC_M1",
    "TICK_MODEL_REAL",
    "TICK_MODEL_TRADING_BAR",
    "TickRecord",
    "TicksGenerator",
    "TimeframeManager",
    "TokenBucketLimiter",
    "aggregate_ticks_to_bars",
    "align_multitimeframe_data",
    "binance_data_list_symbols",
    "check_circuit_breaker_barrier",
    "check_rate_limit",
    "clear_data_cache",
    "create_data_update_job",
    "csv_data_fetch_range",
    "csv_data_load",
    "csv_data_saver_file_exists",
    "csv_data_saver_load",
    "csv_data_saver_save",
    "data_cache_clear",
    "data_cache_get",
    "data_cache_get_path",
    "data_cache_make_key",
    "data_cache_set",
    "data_df",
    "execute_gateway_request",
    "generate_cache_key",
    "generate_synthetic_bars",
    "generate_synthetic_ticks",
    "generate_ticks",
    "generate_ticks_to_parquet",
    "get_cached_data",
    "get_circuit_breaker",
    "get_data",
    "get_data_availability",
    "get_data_dir",
    "get_data_update_job_status",
    "get_feed_status",
    "get_historical_volume",
    "get_market_hours",
    "get_ohlcv_data",
    "get_source_adapter",
    "get_spread_data",
    "get_symbol_metadata",
    "get_tick_data",
    "get_trading_sessions",
    "handle_feed_overflow",
    "label_market_data",
    "labeler_lexlb",
    "list_symbols",
    "load_csv",
    "load_local_dataset",
    "load_ohlcv_csv",
    "load_parquet",
    "normalize_file_records",
    "normalize_numeric",
    "parquet_data_load",
    "parquet_data_saver_file_exists",
    "parquet_data_saver_load",
    "parquet_data_saver_save",
    "recover_crashed_jobs",
    "register_license",
    "register_mock_feed",
    "resample_ohlcv",
    "run_data_update_job_once",
    "save_market_data",
    "set_cached_data",
    "start_data_update_job",
    "stop_data_update_job",
    "timeframe_to_minutes",
    "timeframe_to_pandas_freq",
    "update_circuit_breaker",
    "validate_bars",
    "validate_license",
    "validate_limit",
    "validate_step_alignment",
    "validate_storage_path",
    "validate_timeframe",
    "validate_timezone",
    "validate_utc_timestamp_helper",
]


standardize_domain_exports(globals(), __all__, tool_category="data")
