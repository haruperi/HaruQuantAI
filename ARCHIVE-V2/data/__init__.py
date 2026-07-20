"""Market Data Service.

Provides contract-driven historical, real-time, local, synthetic, and broker
market data interfaces and orchestration.
"""

from collections.abc import Callable

from app.services.data.gateway import (
    get_data,
    get_data_availability,
    get_symbol_metadata,
    list_symbols,
)
from app.services.data.public_api import (
    get_data_tool,
    get_feed_status_tool,
    get_market_hours_tool,
    list_symbols_tool,
)
from app.services.data.scheduler import (
    create_data_update_job,
    get_data_update_job_status,
    get_feed_status,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.storage import (
    clear_data_cache,
    load_local_dataset,
    load_ohlcv_csv,
    save_market_data,
)
from app.services.data.transforms import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    label_market_data,
    resample_ohlcv,
)
from app.services.data.validation import (
    get_market_hours,
    get_trading_sessions,
    validate_bars,
)

OFFICIAL_DATA_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "get_data",
        "list_symbols",
        "get_market_hours",
        "get_feed_status",
    }
)
"""Names intended for the official read-only AI-tool surface."""

OFFICIAL_DATA_TOOLS: dict[str, Callable[..., object]] = {
    "get_data": get_data_tool,
    "list_symbols": list_symbols_tool,
    "get_market_hours": get_market_hours_tool,
    "get_feed_status": get_feed_status_tool,
}
"""Catalog mapping each official tool name to its standard-envelope wrapper.

Wrapper functions live in `app.services.data.public_api` and return the
shared HaruQuant standard tool envelope. Native functions of the same name
(imported above) remain the compatibility surface for existing internal
callers and keep returning native values.
"""

PUBLIC_API_CLASSIFICATION: dict[str, str] = {
    "get_data": "official_tool",
    "list_symbols": "official_tool",
    "get_market_hours": "official_tool",
    "get_feed_status": "official_tool",
    "get_data_tool": "official_tool",
    "list_symbols_tool": "official_tool",
    "get_market_hours_tool": "official_tool",
    "get_feed_status_tool": "official_tool",
    "get_symbol_metadata": "public_support_api",
    "get_data_availability": "public_support_api",
    "get_trading_sessions": "public_support_api",
    "create_data_update_job": "legacy_public_compatibility",
    "get_data_update_job_status": "legacy_public_compatibility",
    "run_data_update_job_once": "legacy_public_compatibility",
    "start_data_update_job": "legacy_public_compatibility",
    "stop_data_update_job": "legacy_public_compatibility",
    "clear_data_cache": "legacy_public_compatibility",
    "load_local_dataset": "legacy_public_compatibility",
    "load_ohlcv_csv": "legacy_public_compatibility",
    "save_market_data": "legacy_public_compatibility",
    "aggregate_ticks_to_bars": "legacy_public_compatibility",
    "align_multitimeframe_data": "legacy_public_compatibility",
    "generate_synthetic_bars": "legacy_public_compatibility",
    "generate_synthetic_ticks": "legacy_public_compatibility",
    "label_market_data": "legacy_public_compatibility",
    "resample_ohlcv": "legacy_public_compatibility",
    "validate_bars": "legacy_public_compatibility",
    "app.services.data.contracts.BrokerMarketDataPort": "internal_only",
}
"""Compatibility classification for root data package attributes."""

__all__ = [
    "aggregate_ticks_to_bars",
    "align_multitimeframe_data",
    "clear_data_cache",
    "create_data_update_job",
    "generate_synthetic_bars",
    "generate_synthetic_ticks",
    "get_data",
    "get_data_availability",
    "get_data_update_job_status",
    "get_feed_status",
    "get_market_hours",
    "get_symbol_metadata",
    "get_trading_sessions",
    "label_market_data",
    "list_symbols",
    "load_local_dataset",
    "load_ohlcv_csv",
    "resample_ohlcv",
    "run_data_update_job_once",
    "save_market_data",
    "start_data_update_job",
    "stop_data_update_job",
    "validate_bars",
]
