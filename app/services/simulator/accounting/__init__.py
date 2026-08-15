"""Supported Simulation accounting API."""

# ruff: noqa: DOC201, DOC501

from app.services.simulator.accounting.calculations import (
    ExecutionCostInput,
    ExecutionCostModel,
    SymbolSpecification,
    ValidatedFXConversionEvidence,
    calculate_execution_costs,
    calculate_margin,
    convert_fx_amount,
    normalize_volume,
    validate_fx_evidence,
)
from app.services.simulator.accounting.ledger import AccountLedger, LedgerFill
from app.services.simulator.accounting.swap import (
    calculate_swap_rollover,
    schedule_rollover,
)
from app.services.simulator.accounting.transactions import (
    TransactionLedger,
    TransactionPosting,
    build_posting,
)


def build_transaction_posting(**fields: object) -> object:
    """Build one immutable signed transaction posting."""
    return build_posting(**fields)


def create_transaction_ledger(initial_balance: object, account_currency: str) -> object:
    """Create one opaque conserved transaction ledger."""
    from decimal import Decimal

    return TransactionLedger(Decimal(str(initial_balance)), account_currency)


def post_transaction(ledger: object, posting: object) -> dict[str, object]:
    """Atomically post one signed transaction."""
    if not isinstance(ledger, TransactionLedger) or not isinstance(
        posting, TransactionPosting
    ):
        raise TypeError("invalid transaction ledger operation")
    return ledger.post(posting)


def serialize_transaction_ledger(ledger: object) -> dict[str, object]:
    """Serialize one transaction ledger."""
    if not isinstance(ledger, TransactionLedger):
        raise TypeError("invalid transaction ledger")
    return ledger.serialize()


def restore_transaction_ledger(state: dict[str, object]) -> object:
    """Restore one transaction ledger from JSON-safe state."""
    return TransactionLedger.restore(state)


__all__ = [
    "AccountLedger",
    "ExecutionCostInput",
    "ExecutionCostModel",
    "LedgerFill",
    "SymbolSpecification",
    "ValidatedFXConversionEvidence",
    "build_transaction_posting",
    "calculate_execution_costs",
    "calculate_margin",
    "calculate_swap_rollover",
    "convert_fx_amount",
    "create_transaction_ledger",
    "normalize_volume",
    "post_transaction",
    "restore_transaction_ledger",
    "schedule_rollover",
    "serialize_transaction_ledger",
    "validate_fx_evidence",
]
