"""Analytics domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.analytics.ports import (
        AnalyzeTradesCapability,
        BulkDatabankCapability,
        CustomPanelsCapability,
        DatabankMembershipCapability,
        ExchangeResultsCapability,
        InterpretResultsCapability,
        MatchResultsCapability,
        QualifyOperationsCapability,
        QueryResultsCapability,
    )

DATABANK_MEMBERSHIP_CAPABILITY: CapabilityKey[DatabankMembershipCapability] = (
    CapabilityKey(
        name="analytics.databank-membership",
        major=1,
    )
)

QUERY_RESULTS_CAPABILITY: CapabilityKey[QueryResultsCapability] = CapabilityKey(
    name="analytics.query-results",
    major=1,
)

INTERPRET_RESULTS_CAPABILITY: CapabilityKey[InterpretResultsCapability] = CapabilityKey(
    name="analytics.interpret-results",
    major=1,
)

ANALYZE_TRADES_CAPABILITY: CapabilityKey[AnalyzeTradesCapability] = CapabilityKey(
    name="analytics.analyze-trades",
    major=1,
)

EXCHANGE_RESULTS_CAPABILITY: CapabilityKey[ExchangeResultsCapability] = CapabilityKey(
    name="analytics.exchange-results",
    major=1,
)

BULK_DATABANK_CAPABILITY: CapabilityKey[BulkDatabankCapability] = CapabilityKey(
    name="analytics.bulk-databank",
    major=1,
)

MATCH_RESULTS_CAPABILITY: CapabilityKey[MatchResultsCapability] = CapabilityKey(
    name="analytics.match-results",
    major=1,
)

CUSTOM_PANELS_CAPABILITY: CapabilityKey[CustomPanelsCapability] = CapabilityKey(
    name="analytics.custom-panels",
    major=1,
)

QUALIFY_OPERATIONS_CAPABILITY: CapabilityKey[QualifyOperationsCapability] = (
    CapabilityKey(
        name="analytics.qualify-operations",
        major=1,
    )
)
