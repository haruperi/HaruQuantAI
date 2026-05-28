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
    # parquet.py tools and helpers
    "get_data_dir",
    "load_parquet",
    "parquet_data_load",
    "parquet_data_saver_file_exists",
    "parquet_data_saver_load",
    "parquet_data_saver_save",
]
