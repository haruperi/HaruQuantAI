"""Focused loading of approved local DATA artifacts."""

from app.services.data.datasets.catalog import (
    get_catalog_evidence,
    get_catalog_table_lifecycles,
    get_instrument_spec,
    get_provider_specification_revision,
    get_provider_specification_revisions,
    get_verified_research_source,
    list_brokers,
    list_instruments,
    list_market_series,
    list_verified_datasets,
    reconcile_data_catalog,
    record_catalog_fetch,
    record_catalog_quality_event,
    register_catalog_artifact,
    register_provider_specification_revision,
    sync_catalog_reference,
    update_instrument_spec,
    update_market_series,
)
from app.services.data.datasets.contracts import (
    DatasetLoadRequest,
    ManifestCompatibility,
)
from app.services.data.datasets.csv_loader import load_csv
from app.services.data.datasets.manifest import verify_manifest_compatibility
from app.services.data.datasets.parquet_loader import load_parquet
from app.services.data.persistence.dataset_writer import (
    load_dataset,
    load_local_dataset,
)

__all__ = [
    "DatasetLoadRequest",
    "ManifestCompatibility",
    "get_catalog_evidence",
    "get_catalog_table_lifecycles",
    "get_instrument_spec",
    "get_provider_specification_revision",
    "get_provider_specification_revisions",
    "get_verified_research_source",
    "list_brokers",
    "list_instruments",
    "list_market_series",
    "list_verified_datasets",
    "load_csv",
    "load_dataset",
    "load_local_dataset",
    "load_parquet",
    "reconcile_data_catalog",
    "record_catalog_fetch",
    "record_catalog_quality_event",
    "register_catalog_artifact",
    "register_provider_specification_revision",
    "sync_catalog_reference",
    "update_instrument_spec",
    "update_market_series",
    "verify_manifest_compatibility",
]
