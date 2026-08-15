"""Signed account-currency transaction postings and conserved audit ledger."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import canonical_digest

type TransactionKind = Literal[
    "profit",
    "commission",
    "fees",
    "swap",
    "tax",
    "rebates",
    "deposit",
    "withdrawal",
    "credit",
    "correction",
]

_POSITIVE_KINDS = frozenset({"profit", "rebates", "deposit", "credit"})
_NEGATIVE_KINDS = frozenset({"commission", "fees", "swap", "tax", "withdrawal"})


class TransactionPosting(BaseModel):
    """One immutable signed account-currency economic posting."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    posting_id: str
    economic_at: datetime
    source_at: datetime
    account_currency: str
    amount: Decimal
    kind: TransactionKind
    source_sequence: int
    evidence_reference: str
    causal_order_id: str | None = None
    causal_deal_id: str | None = None
    causal_position_id: str | None = None
    authority_id: str | None = None

    @field_validator("economic_at", "source_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        """Require aware UTC timestamps."""
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("transaction timestamps must be aware UTC")
        return value

    @model_validator(mode="after")
    def _invariants(self) -> Self:
        """Validate signed posting identity and causal order."""
        text = (self.posting_id, self.account_currency, self.evidence_reference)
        if any(not value or value != value.strip() for value in text):
            raise ValueError("transaction identity and evidence are required")
        if not self.amount.is_finite() or self.amount == 0:
            raise ValueError("transaction amount must be finite and non-zero")
        if self.kind in _POSITIVE_KINDS and self.amount < 0:
            raise ValueError("credit transaction amount must be positive")
        if self.kind in _NEGATIVE_KINDS and self.amount > 0:
            raise ValueError("debit transaction amount must be negative")
        if self.source_sequence < 0 or self.source_at < self.economic_at:
            raise ValueError("transaction causal order is invalid")
        return self


class TransactionLedger:
    """Atomic signed ledger with equal-and-opposite audit entries."""

    def __init__(self, initial_balance: Decimal, account_currency: str) -> None:
        """Initialize a transaction ledger from explicit account evidence."""
        if not initial_balance.is_finite() or initial_balance < 0:
            raise ValueError("initial balance must be finite and non-negative")
        if not account_currency or account_currency != account_currency.strip():
            raise ValueError("account currency is invalid")
        self._initial_balance = initial_balance
        self._account_currency = account_currency
        self._postings: list[TransactionPosting] = []
        self._posting_ids: set[str] = set()
        self._last_source_sequence = -1

    def post(self, posting: TransactionPosting) -> dict[str, object]:
        """Atomically admit one posting after every invariant is verified."""
        if posting.posting_id in self._posting_ids:
            raise ValueError("duplicate transaction posting identity")
        if posting.account_currency != self._account_currency:
            raise ValueError("transaction currency does not match ledger")
        if posting.source_sequence <= self._last_source_sequence:
            raise ValueError("transaction source sequence is not increasing")
        self._postings.append(posting)
        self._posting_ids.add(posting.posting_id)
        self._last_source_sequence = posting.source_sequence
        return self.snapshot()

    def snapshot(self) -> dict[str, object]:
        """Return JSON-safe totals and conserved audit entries."""
        posting_total = sum((item.amount for item in self._postings), Decimal(0))
        audit_entries = tuple(
            {
                "posting_id": item.posting_id,
                "cash": str(item.amount),
                "economic_counteraccount": str(-item.amount),
            }
            for item in self._postings
        )
        conservation = sum(
            (
                Decimal(entry["cash"]) + Decimal(entry["economic_counteraccount"])
                for entry in audit_entries
            ),
            Decimal(0),
        )
        if conservation != 0:
            raise ValueError("transaction audit representation is not conserved")
        return {
            "account_currency": self._account_currency,
            "balance": str(self._initial_balance + posting_total),
            "posting_total": str(posting_total),
            "conservation": str(conservation),
            "last_source_sequence": self._last_source_sequence,
            "postings": tuple(item.model_dump(mode="json") for item in self._postings),
            "audit_entries": audit_entries,
        }

    def serialize(self) -> dict[str, object]:
        """Return complete deterministic restore material."""
        return {
            "initial_balance": str(self._initial_balance),
            **self.snapshot(),
        }

    @classmethod
    def restore(cls, state: dict[str, object]) -> TransactionLedger:
        """Restore one ledger through the same admission invariants."""
        ledger = cls(
            Decimal(str(state["initial_balance"])), str(state["account_currency"])
        )
        postings = state.get("postings")
        if not isinstance(postings, (tuple, list)):
            raise TypeError("transaction postings state is invalid")
        for value in postings:
            ledger.post(TransactionPosting.model_validate(value))
        return ledger


def build_posting(**fields: object) -> TransactionPosting:
    """Build one posting, deriving identity only when complete material exists."""
    material = dict(fields)
    material.setdefault("posting_id", "txn-" + canonical_digest(material))
    return TransactionPosting.model_validate(material)


__all__ = ["TransactionLedger", "TransactionPosting", "build_posting"]
