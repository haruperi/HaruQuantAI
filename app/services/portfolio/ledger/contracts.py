"""Versioned Portfolio ledger and account transport contracts.

Implements ``FEAT-PORT-09`` (``TC-IMP-PORT-01``, ``TC-IMP-PORT-02``). Cross-domain
contracts travel as validated JSON-safe mappings behind ``build_*``/``parse_*``
function pairs per architectural decision D-1. Internal Pydantic models stay
private; only the standalone build/parse functions are exported.

Each posting type names an economic event the ledger consumes exactly once
(``TC-IMP-PORT-01``). Corrections are ``correction`` or reversal postings and
never mutate a prior row; financial records are append-only.
"""

# mypy: disable-error-code="arg-type"

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import get_logger, to_json_safe

logger = get_logger(__name__)

# Posting type catalogue (gap TC-IMP-PORT-01). Every posting names one economic
# event; ``correction`` reverses or amends without editing prior rows.
PostingType = Literal[
    "deposit",
    "withdrawal",
    "fill",
    "commission",
    "fee",
    "spread",
    "financing",
    "funding",
    "borrow",
    "dividend",
    "fx_translation",
    "mark_to_market",
    "settlement",
    "corporate_action",
    "liquidation",
    "correction",
]

Side = Literal["debit", "credit"]

# Minimum legs in a balanced double-entry batch (a debit and a credit leg).
_MIN_BALANCED_ENTRIES = 2

_CURRENCY_RE = __import__("re").compile(r"^[A-Z]{3,8}\Z")


def _text(value: str, label: str) -> str:
    """Validate non-empty trimmed text.

    Args:
        value: Candidate text.
        label: Safe field label for diagnostics.

    Returns:
        Validated text.

    Raises:
        ValueError: If text is empty or untrimmed.
    """
    if not value or value != value.strip():
        message = f"{label} must be non-empty trimmed text"
        raise ValueError(message)
    return value


def _currency(value: str, label: str) -> str:
    """Validate an ISO-style currency or asset code.

    Args:
        value: Candidate currency code.
        label: Safe field label for diagnostics.

    Returns:
        Validated uppercase code.

    Raises:
        ValueError: If the code is malformed.
    """
    if _CURRENCY_RE.fullmatch(value) is None:
        message = f"{label} must be an uppercase 3-8 letter currency/asset code"
        raise ValueError(message)
    return value


def _decimal(value: Decimal, label: str) -> Decimal:
    """Validate one finite Decimal amount.

    Args:
        value: Candidate amount.
        label: Safe field label for diagnostics.

    Returns:
        Validated finite Decimal.

    Raises:
        ValueError: If the value is non-finite.
    """
    if not isinstance(value, Decimal) or not value.is_finite():
        message = f"{label} must be a finite Decimal"
        raise ValueError(message)
    return value


def _utc(value: datetime, label: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        label: Safe field label for diagnostics.

    Returns:
        Validated UTC timestamp.

    Raises:
        ValueError: If the timestamp is naive or non-UTC.
    """
    if not isinstance(value, datetime) or value.tzinfo is None:
        message = f"{label} must be aware UTC"
        raise ValueError(message)
    if value.utcoffset() != timedelta(0):
        message = f"{label} must be UTC"
        raise ValueError(message)
    return value


class _LedgerEntry(BaseModel):
    """Private immutable single-sided posting leg (``LedgerEntry v1``).

    One leg of a balanced double-entry posting. Legs are grouped into a
    ``PostingBatch`` that must sum to zero per currency.

    Attributes:
        entry_id: Stable immutable leg identity.
        account_id: Chart-of-accounts identity the leg posts to.
        side: ``debit`` or ``credit``.
        amount: Non-negative finite Decimal magnitude.
        currency: Uppercase currency/asset code.
        posting_type: Economic posting-type catalogue value.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.ledger_entry.v1"] = "portfolio.ledger_entry.v1"
    entry_id: str
    account_id: str
    side: Side
    amount: Decimal
    currency: str
    posting_type: PostingType

    @field_validator("entry_id", "account_id")
    @classmethod
    def _text(cls, value: str) -> str:
        """Validate one identity field.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        return _text(value, "ledger entry identity")

    @field_validator("currency")
    @classmethod
    def _currency_field(cls, value: str) -> str:
        """Validate one currency code.

        Args:
            value: Candidate code.

        Returns:
            Validated code.
        """
        return _currency(value, "ledger entry currency")

    @field_validator("amount")
    @classmethod
    def _amount(cls, value: Decimal) -> Decimal:
        """Validate a non-negative finite magnitude.

        Args:
            value: Candidate magnitude.

        Returns:
            Validated magnitude.

        Raises:
            ValueError: If the magnitude is negative.
        """
        parsed = _decimal(value, "ledger entry amount")
        if parsed < 0:
            raise ValueError("ledger entry amount cannot be negative")
        return parsed


class _PostingBatch(BaseModel):
    """Private immutable balanced posting batch (``PostingBatch v1``).

    A batch groups two or more legs that must sum to zero per currency. Batches
    are append-only; a ``correction`` batch reverses or amends a prior batch by
    reference without editing it.

    Attributes:
        batch_id: Immutable batch identity.
        source_event_id: External economic event identity (Trading/Broker/Simulator).
        source_sequence: Exactly-once monotonic sequence for ``source_event_id``.
        entry_sequence: Internal monotonically increasing entry index.
        reversal_of: Optional prior batch reversed by this correction batch.
        entries: Ordered legs (>= 2) grouped by this batch.
        posted_at: UTC posting timestamp.
        canonical_hash: Stable canonical digest of the batch.
        request_id: Request trace identity.
        correlation_id: Correlation trace identity.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.posting_batch.v1"] = "portfolio.posting_batch.v1"
    batch_id: str
    source_event_id: str
    source_sequence: int
    entry_sequence: int
    reversal_of: str | None = None
    entries: tuple[_LedgerEntry, ...]
    posted_at: datetime
    canonical_hash: str
    request_id: str
    correlation_id: str

    @field_validator("batch_id", "source_event_id", "request_id", "correlation_id")
    @classmethod
    def _text(cls, value: str) -> str:
        """Validate one identity field.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        return _text(value, "posting batch identity")

    @field_validator("source_sequence", "entry_sequence")
    @classmethod
    def _sequence(cls, value: int) -> int:
        """Validate a positive monotonic sequence.

        Args:
            value: Candidate sequence.

        Returns:
            Validated sequence.

        Raises:
            ValueError: If the sequence is not positive.
        """
        if value <= 0:
            raise ValueError("posting batch sequence must be positive")
        return value

    @field_validator("reversal_of")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        """Validate an optional reversal reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference or ``None``.
        """
        return None if value is None else _text(value, "reversal reference")

    @field_validator("posted_at")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        """Validate a UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "posting batch timestamp")

    @model_validator(mode="after")
    def _validate_balance(self) -> _PostingBatch:
        """Validate the balanced double-entry and identity invariants.

        Returns:
            Validated batch.

        Raises:
            ValueError: If legs are missing, duplicated, or unbalanced.
        """
        logger.debug("Validating posting batch balance")
        if len(self.entries) < _MIN_BALANCED_ENTRIES:
            raise ValueError("posting batch requires at least two entries")
        entry_ids = tuple(entry.entry_id for entry in self.entries)
        if len(set(entry_ids)) != len(entry_ids):
            raise ValueError("posting batch entries must be unique")
        currencies: set[str] = set()
        for currency in (entry.currency for entry in self.entries):
            currencies.add(currency)
        totals: dict[str, Decimal] = {}
        for entry in self.entries:
            signed = entry.amount if entry.side == "debit" else -entry.amount
            totals[entry.currency] = totals.get(entry.currency, Decimal(0)) + signed
        for currency, total in totals.items():
            if total != 0:
                message = f"posting batch must balance to zero for {currency}"
                raise ValueError(message)
        if not currencies:
            raise ValueError("posting batch must post at least one currency")
        if self.reversal_of == self.batch_id:
            raise ValueError("posting batch cannot reverse itself")
        return self


class _LedgerAccount(BaseModel):
    """Private immutable chart-of-accounts entry (``LedgerAccount v1``).

    Attributes:
        account_id: Stable chart-of-accounts identity.
        portfolio_id: Owning Portfolio identity.
        currency: Accounting currency for the account.
        normal_balance: ``debit`` or ``credit`` natural side.
        category: Account category (asset, liability, equity, income, expense).
        registered_at: UTC registration timestamp.
        request_id: Request trace identity.
        correlation_id: Correlation trace identity.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.ledger_account.v1"] = "portfolio.ledger_account.v1"
    account_id: str
    portfolio_id: str
    currency: str
    normal_balance: Side
    category: Literal["asset", "liability", "equity", "income", "expense"]
    registered_at: datetime
    request_id: str
    correlation_id: str

    @field_validator("account_id", "portfolio_id", "request_id", "correlation_id")
    @classmethod
    def _text(cls, value: str) -> str:
        """Validate one identity field.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        return _text(value, "ledger account identity")

    @field_validator("currency")
    @classmethod
    def _currency_field(cls, value: str) -> str:
        """Validate one currency code.

        Args:
            value: Candidate code.

        Returns:
            Validated code.
        """
        return _currency(value, "ledger account currency")

    @field_validator("registered_at")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        """Validate a UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "ledger account timestamp")


def build_ledger_entry(
    *,
    entry_id: str,
    account_id: str,
    side: str,
    amount: Decimal,
    currency: str,
    posting_type: str,
) -> dict[str, Any]:
    """Build a validated JSON-safe ``LedgerEntry v1`` mapping.

    Args:
        entry_id: Stable immutable leg identity.
        account_id: Chart-of-accounts identity.
        side: ``debit`` or ``credit``.
        amount: Non-negative finite Decimal magnitude.
        currency: Uppercase currency/asset code.
        posting_type: Economic posting-type catalogue value.

    Returns:
        JSON-safe mapping.

    Raises:
        ValueError: If the leg is invalid.
    """
    logger.info("Building LedgerEntry contract")
    model = _LedgerEntry(
        entry_id=entry_id,
        account_id=account_id,
        side=side,
        amount=amount,
        currency=currency,
        posting_type=posting_type,
    )
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_ledger_entry(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict ``LedgerEntry v1`` mapping.

    Args:
        value: Candidate mapping.

    Returns:
        JSON-safe mapping.

    Raises:
        ValueError: If the mapping is incompatible.
    """
    logger.info("Parsing LedgerEntry contract")
    model = _LedgerEntry.model_validate(dict(value))
    return dict(to_json_safe(model.model_dump(mode="json")))


def build_posting_batch(
    *,
    batch_id: str,
    source_event_id: str,
    source_sequence: int,
    entry_sequence: int,
    entries: Sequence[Mapping[str, object]],
    posted_at: datetime,
    canonical_hash: str,
    request_id: str,
    correlation_id: str,
    reversal_of: str | None = None,
) -> dict[str, Any]:
    """Build a validated JSON-safe ``PostingBatch v1`` mapping.

    Args:
        batch_id: Immutable batch identity.
        source_event_id: External economic event identity.
        source_sequence: Exactly-once monotonic event sequence.
        entry_sequence: Internal monotonically increasing entry index.
        entries: Ordered leg mappings (>= 2).
        posted_at: UTC posting timestamp.
        canonical_hash: Stable canonical digest of the batch.
        request_id: Request trace identity.
        correlation_id: Correlation trace identity.
        reversal_of: Optional prior batch reversed by this correction batch.

    Returns:
        JSON-safe mapping.

    Raises:
        ValueError: If the batch is invalid or unbalanced.
    """
    logger.info("Building PostingBatch contract")
    leg_models = tuple(_LedgerEntry.model_validate(dict(item)) for item in entries)
    model = _PostingBatch(
        batch_id=batch_id,
        source_event_id=source_event_id,
        source_sequence=source_sequence,
        entry_sequence=entry_sequence,
        reversal_of=reversal_of,
        entries=leg_models,
        posted_at=posted_at,
        canonical_hash=canonical_hash,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_posting_batch(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict ``PostingBatch v1`` mapping.

    Args:
        value: Candidate mapping.

    Returns:
        JSON-safe mapping.

    Raises:
        ValueError: If the mapping is incompatible or unbalanced.
    """
    logger.info("Parsing PostingBatch contract")
    model = _PostingBatch.model_validate(dict(value))
    return dict(to_json_safe(model.model_dump(mode="json")))


def build_ledger_account(
    *,
    account_id: str,
    portfolio_id: str,
    currency: str,
    normal_balance: str,
    category: str,
    registered_at: datetime,
    request_id: str,
    correlation_id: str,
) -> dict[str, Any]:
    """Build a validated JSON-safe ``LedgerAccount v1`` mapping.

    Args:
        account_id: Chart-of-accounts identity.
        portfolio_id: Owning Portfolio identity.
        currency: Accounting currency.
        normal_balance: ``debit`` or ``credit`` natural side.
        category: Account category.
        registered_at: UTC registration timestamp.
        request_id: Request trace identity.
        correlation_id: Correlation trace identity.

    Returns:
        JSON-safe mapping.

    Raises:
        ValueError: If the account is invalid.
    """
    logger.info("Building LedgerAccount contract")
    model = _LedgerAccount(
        account_id=account_id,
        portfolio_id=portfolio_id,
        currency=currency,
        normal_balance=normal_balance,
        category=category,
        registered_at=registered_at,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_ledger_account(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict ``LedgerAccount v1`` mapping.

    Args:
        value: Candidate mapping.

    Returns:
        JSON-safe mapping.

    Raises:
        ValueError: If the mapping is incompatible.
    """
    logger.info("Parsing LedgerAccount contract")
    model = _LedgerAccount.model_validate(dict(value))
    return dict(to_json_safe(model.model_dump(mode="json")))


__all__: tuple[str, ...] = (
    "build_ledger_account",
    "build_ledger_entry",
    "build_posting_batch",
    "parse_ledger_account",
    "parse_ledger_entry",
    "parse_posting_batch",
)
