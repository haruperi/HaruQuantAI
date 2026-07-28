"""Indicators-owned immutable error definitions for standard responses."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from app.utils import validate_error_catalog


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Immutable domain-owned error catalogue entry."""

    code: str
    domain: str
    description: str
    category: str
    severity: Literal["info", "warning", "error", "critical"]
    retryable: bool
    operator_action: str


_DEFINITIONS = (
    ErrorDefinition(
        code="IND_INVALID_CONFIG",
        domain="indicators",
        description="The indicator configuration is invalid",
        category="configuration",
        severity="error",
        retryable=False,
        operator_action="Correct the indicator configuration before retrying",
    ),
    ErrorDefinition(
        code="IND_INVALID_PARAMETER",
        domain="indicators",
        description="An indicator parameter is invalid",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Correct the supplied indicator parameters",
    ),
    ErrorDefinition(
        code="IND_UNSUPPORTED_INDICATOR",
        domain="indicators",
        description="The requested indicator is not officially supported",
        category="capability",
        severity="warning",
        retryable=False,
        operator_action="Select an indicator from the official registry",
    ),
    ErrorDefinition(
        code="IND_UNSUPPORTED_TIMEFRAME",
        domain="indicators",
        description="The source timeframe is not supported by the indicator",
        category="capability",
        severity="warning",
        retryable=False,
        operator_action="Supply a dataset with the required timeframe",
    ),
    ErrorDefinition(
        code="IND_UNSUPPORTED_DTYPE",
        domain="indicators",
        description="Input values cannot be represented by the supported dtype",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Supply finite numeric input values",
    ),
    ErrorDefinition(
        code="IND_INVALID_INPUT_SCHEMA",
        domain="indicators",
        description="The input dataset does not satisfy MarketDataset v1",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Supply a validated MarketDataset v1 dataset",
    ),
    ErrorDefinition(
        code="IND_MISSING_REQUIRED_COLUMN",
        domain="indicators",
        description="A required input column is missing",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Supply all columns required by the indicator",
    ),
    ErrorDefinition(
        code="IND_INVALID_OUTPUT_COLUMN",
        domain="indicators",
        description="The calculated output column name is invalid",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Use the official output naming contract",
    ),
    ErrorDefinition(
        code="IND_OUTPUT_COLUMN_CONFLICT",
        domain="indicators",
        description="An indicator output column conflicts with an existing column",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Choose a non-conflicting output configuration",
    ),
    ErrorDefinition(
        code="IND_INVALID_OUTPUT_MODE",
        domain="indicators",
        description="The requested output mode is unsupported",
        category="configuration",
        severity="error",
        retryable=False,
        operator_action="Use the supported copy or values output mode",
    ),
    ErrorDefinition(
        code="IND_INPUT_MUTATION_DETECTED",
        domain="indicators",
        description="The input dataset no longer matches the calculation identity",
        category="integrity",
        severity="error",
        retryable=False,
        operator_action="Recalculate against the unchanged source dataset",
    ),
    ErrorDefinition(
        code="IND_DUPLICATE_TIMESTAMP",
        domain="indicators",
        description="Input records contain duplicate timestamps",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Provide records with unique timestamps",
    ),
    ErrorDefinition(
        code="IND_NON_MONOTONIC_TIME",
        domain="indicators",
        description="Input timestamps are not strictly increasing",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Order the dataset records by increasing timestamp",
    ),
    ErrorDefinition(
        code="IND_AMBIGUOUS_TIMESTAMP",
        domain="indicators",
        description="Input timestamps cannot be represented unambiguously",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Supply unambiguous UTC timestamps",
    ),
    ErrorDefinition(
        code="IND_INVALID_TIMEZONE",
        domain="indicators",
        description="Input timestamps are not UTC-aware",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Normalize input timestamps to UTC",
    ),
    ErrorDefinition(
        code="IND_INVALID_OHLC",
        domain="indicators",
        description="Input OHLC values violate an indicator invariant",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Correct the invalid OHLC values",
    ),
    ErrorDefinition(
        code="IND_INSUFFICIENT_DATA",
        domain="indicators",
        description="The dataset contains no usable observations",
        category="validation",
        severity="warning",
        retryable=True,
        operator_action="Retrieve a non-empty normalized dataset",
    ),
    ErrorDefinition(
        code="IND_LOOKAHEAD_RISK",
        domain="indicators",
        description="The requested calculation would use unavailable future data",
        category="safety",
        severity="critical",
        retryable=False,
        operator_action="Remove the lookahead dependency before retrying",
    ),
    ErrorDefinition(
        code="IND_FORMULA_VERSION_MISMATCH",
        domain="indicators",
        description="The requested formula version is not the official version",
        category="compatibility",
        severity="error",
        retryable=False,
        operator_action="Use the formula version declared by the registry",
    ),
    ErrorDefinition(
        code="IND_RESOURCE_LIMIT_EXCEEDED",
        domain="indicators",
        description="The calculation exceeds an approved resource limit",
        category="resource",
        severity="error",
        retryable=False,
        operator_action="Reduce the request to the approved resource bounds",
    ),
    ErrorDefinition(
        code="IND_PARTIAL_RESULT",
        domain="indicators",
        description="The calculation did not produce an atomic complete result",
        category="integrity",
        severity="critical",
        retryable=False,
        operator_action="Inspect the redacted diagnostic evidence",
    ),
    ErrorDefinition(
        code="IND_INTERNAL_ERROR",
        domain="indicators",
        description="The indicator operation failed unexpectedly",
        category="internal",
        severity="critical",
        retryable=False,
        operator_action="Inspect redacted diagnostic evidence",
    ),
)

INDICATOR_ERROR_CATALOG = validate_error_catalog(
    MappingProxyType({definition.code: definition for definition in _DEFINITIONS})
)

__all__ = ["INDICATOR_ERROR_CATALOG"]
