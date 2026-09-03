"""Feature specification for Partitioned Parquet Market Data Store."""

from app.contracts.data.capabilities import MARKET_DATA_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-MARKET_DATA_STORE",
    domain="data",
    provides=frozenset({MARKET_DATA_STORE_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Canonical partitioned Parquet market data store with Zstandard (ZSTD) "
        "compression, fixed-point integer ticks, PyArrow immutable append writer, "
        "Polars lazy reader, DuckDB SQL analytics, and DuckDB manifest catalog."
    ),
    state=StateDeclaration(
        namespace="data.market_data_store",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Canonical partitioned Parquet market data files and "
            "DuckDB ingestion manifest."
        ),
    ),
    config_keys=frozenset(
        {
            "storage_root",
            "compression",
            "compression_level",
            "min_rows_per_group",
            "max_rows_per_group",
            "max_rows_per_file",
            "manifest_database_path",
            "staging_dir_name",
        }
    ),
)
