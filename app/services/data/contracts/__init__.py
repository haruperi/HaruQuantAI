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
from app.services.data.contracts.responses import (
    OPERATION_TRAITS,
    OperationTraits,
    build_data_response,
    build_exception_response,
    data_start_time,
    resolve_operation_request_id,
    run_data_operation,
    run_data_operation_async,
    unwrap_data_response,
)

__all__ = [
    "DATA_ERROR_MANIFEST",
    "ERROR_SAFE_DETAILS_MAX_BYTES",
    "ERROR_SAFE_DETAILS_MAX_ITEMS",
    "MARKET_DATASET_SCHEMA",
    "NORMALIZATION_VERSION",
    "OPERATION_TRAITS",
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
    "OperationTraits",
    "QualityIssue",
    "SpreadRecord",
    "TickRecord",
    "build_data_response",
    "build_exception_response",
    "data_start_time",
    "resolve_operation_request_id",
    "run_data_operation",
    "run_data_operation_async",
    "unwrap_data_response",
]
