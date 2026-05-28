"""Data tools exposed to HaruQuantAI agents.

This package is the official public registry for approved AI-callable tools in
``tools.data``. Implementation logic must live in normal module files; this
registry should only import and expose approved tools.
"""

# csv.py tools and helpers
from tools.data.csv import (
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

# dukascopy.py tools
from tools.data.dukascopy import (
    dukascopy_data_list_symbols,
    dukascopy_data_load,
    dukascopy_data_resolve_instrument,
)

# generators.py tools
from tools.data.generators import data_generate_ticks, gbm_data_generate

# mt5.py tools
from tools.data.mt5 import (
    mt5_connection_check,
    mt5_data_get_bars,
    mt5_data_list_symbol_details,
    mt5_data_list_symbols,
)

# parquet.py tools and helpers
from tools.data.parquet import (
    get_data_dir,
    load_parquet,
    parquet_data_load,
    parquet_data_saver_file_exists,
    parquet_data_saver_load,
    parquet_data_saver_save,
)

__all__ = [
    # csv.py tools and helpers
    "CSVDataSource",
    "clear_data_cache",
    "csv_data_fetch_range",
    "csv_data_load",
    "csv_data_saver_file_exists",
    "csv_data_saver_load",
    "csv_data_saver_save",
    "get_cached_data",
    "load_csv",
    # dukascopy.py tools
    "dukascopy_data_list_symbols",
    "dukascopy_data_load",
    "dukascopy_data_resolve_instrument",
    # generators.py tools
    "data_generate_ticks",
    "gbm_data_generate",
    # mt5.py tools
    "mt5_connection_check",
    "mt5_data_get_bars",
    "mt5_data_list_symbol_details",
    "mt5_data_list_symbols",
    # parquet.py tools and helpers
    "get_data_dir",
    "load_parquet",
    "parquet_data_load",
    "parquet_data_saver_file_exists",
    "parquet_data_saver_load",
    "parquet_data_saver_save",
]
