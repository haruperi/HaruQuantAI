"""Canonical, provider-neutral DATA contract vocabulary."""

from app.services.data.contracts.dataset import (
    MARKET_DATASET_SCHEMA,
    NORMALIZATION_VERSION,
    PRECISION_POLICIES,
    QUALITY_SAMPLE_LIMIT,
    WORKFLOW_CONTEXTS,
    DataGap,
    DataQualityReport,
    DataRange,
    MarketDataset,
    QualityIssue,
)
from app.services.data.contracts.errors import (
    DATA_ERROR_MANIFEST,
    ERROR_SAFE_DETAILS_MAX_BYTES,
    ERROR_SAFE_DETAILS_MAX_ITEMS,
    DataError,
    ErrorDefinition,
)
from app.services.data.contracts.records import OHLCVRecord, SpreadRecord, TickRecord

__all__ = [
    "DATA_ERROR_MANIFEST",
    "ERROR_SAFE_DETAILS_MAX_BYTES",
    "ERROR_SAFE_DETAILS_MAX_ITEMS",
    "MARKET_DATASET_SCHEMA",
    "NORMALIZATION_VERSION",
    "PRECISION_POLICIES",
    "QUALITY_SAMPLE_LIMIT",
    "WORKFLOW_CONTEXTS",
    "DataError",
    "DataGap",
    "DataQualityReport",
    "DataRange",
    "ErrorDefinition",
    "MarketDataset",
    "OHLCVRecord",
    "QualityIssue",
    "SpreadRecord",
    "TickRecord",
]
