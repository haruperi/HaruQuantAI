"""Account balance and cash computation for the Portfolio ledger.

Implements ``TC-IMP-PORT-03``: settled and unsettled cash, accrued income and
costs, and reproducible balance rebuild. Cash postings are tagged with a
``settlement`` or operational posting type so balances can be split into
settled and unsettled (pending) components.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from app.services.portfolio.ledger.postings import _signed_amount, recompute_balances
from app.utils import get_logger

logger = get_logger(__name__)

# Posting types that move settled cash versus pending/unsettled cash. A ``fill``
# or ``settlement`` posting settles cash; other operational postings (deposit,
# withdrawal, financing, etc.) are treated as settled on posting by default and
# are separated here only when a settlement leg is present.
_SETTLED_TYPES = frozenset(
    {
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
    }
)
# Accrued income/cost posting types surfaced separately on the cash view.
_ACCRUED_INCOME_TYPES = frozenset({"dividend", "funding"})
_ACCRUED_COST_TYPES = frozenset({"financing", "borrow", "commission", "fee", "spread"})


@dataclass(frozen=True, slots=True)
class CashBalance:
    """Reproducible per-currency cash balance view.

    Attributes:
        account_id: Chart-of-accounts identity.
        currency: Cash currency.
        settled: Settled debit-minus-credit signed balance.
        unsettled: Pending debit-minus-credit signed balance.
        accrued_income: Accumulated income postings.
        accrued_cost: Accumulated cost postings.
    """

    account_id: str
    currency: str
    settled: Decimal
    unsettled: Decimal
    accrued_income: Decimal
    accrued_cost: Decimal


def _filter_entries(
    entries: Sequence[Mapping[str, object]],
    *,
    account_id: str | None = None,
    currency: str | None = None,
    posting_types: frozenset[str] | None = None,
) -> list[Mapping[str, object]]:
    """Return legs matching the supplied filters.

    Args:
        entries: Ordered leg mappings.
        account_id: Optional account filter.
        currency: Optional currency filter.
        posting_types: Optional posting-type allowlist.

    Returns:
        Filtered leg list.
    """
    filtered: list[Mapping[str, object]] = []
    for entry in entries:
        if account_id is not None and str(entry.get("account_id", "")) != account_id:
            continue
        if currency is not None and str(entry.get("currency", "")) != currency:
            continue
        if (
            posting_types is not None
            and str(entry.get("posting_type", "")) not in posting_types
        ):
            continue
        filtered.append(entry)
    return filtered


def settled_balance(
    entries: Sequence[Mapping[str, object]],
    account_id: str,
    currency: str,
) -> Decimal:
    """Return the settled signed cash balance for one account/currency.

    Args:
        entries: Ordered leg mappings scoped to the account.
        account_id: Account to compute for.
        currency: Cash currency.

    Returns:
        Signed debit-minus-credit settled balance.
    """
    logger.debug("Computing settled balance for %s %s", account_id, currency)
    filtered = _filter_entries(
        entries,
        account_id=account_id,
        currency=currency,
        posting_types=_SETTLED_TYPES,
    )
    total = Decimal(0)
    for entry in filtered:
        total += _signed_amount(entry)
    return total


def unsettled_balance(
    entries: Sequence[Mapping[str, object]],
    account_id: str,
    currency: str,
) -> Decimal:
    """Return the pending (unsettled) signed cash balance.

    Legs without an explicit ``settlement`` posting and not in the settled
    catalogue are treated as pending. In the v1 catalogue every operational
    posting settles on posting, so the unsettled component is zero unless a
    future posting type introduces pending cash; the function is provided so
    the cash view is forward-compatible and explicit about the split.

    Args:
        entries: Ordered leg mappings scoped to the account.
        account_id: Account to compute for.
        currency: Cash currency.

    Returns:
        Signed debit-minus-credit unsettled balance.
    """
    logger.debug("Computing unsettled balance for %s %s", account_id, currency)
    total = Decimal(0)
    for entry in _filter_entries(entries, account_id=account_id, currency=currency):
        if str(entry.get("posting_type", "")) not in _SETTLED_TYPES:
            total += _signed_amount(entry)
    return total


def accrued_income(
    entries: Sequence[Mapping[str, object]],
    account_id: str,
    currency: str,
) -> Decimal:
    """Return accumulated income postings (dividends, funding income).

    Args:
        entries: Ordered leg mappings scoped to the account.
        account_id: Account to compute for.
        currency: Cash currency.

    Returns:
        Signed debit-minus-credit accrued income.
    """
    filtered = _filter_entries(
        entries,
        account_id=account_id,
        currency=currency,
        posting_types=_ACCRUED_INCOME_TYPES,
    )
    total = Decimal(0)
    for entry in filtered:
        total += _signed_amount(entry)
    return total


def accrued_cost(
    entries: Sequence[Mapping[str, object]],
    account_id: str,
    currency: str,
) -> Decimal:
    """Return accumulated cost postings (financing, borrow, commissions, fees).

    Args:
        entries: Ordered leg mappings scoped to the account.
        account_id: Account to compute for.
        currency: Cash currency.

    Returns:
        Signed debit-minus-credit accrued cost.
    """
    filtered = _filter_entries(
        entries,
        account_id=account_id,
        currency=currency,
        posting_types=_ACCRUED_COST_TYPES,
    )
    total = Decimal(0)
    for entry in filtered:
        total += _signed_amount(entry)
    return total


def cash_balance(
    entries: Sequence[Mapping[str, object]],
    account_id: str,
    currency: str,
) -> CashBalance:
    """Return the complete reproducible cash balance view.

    Args:
        entries: Ordered leg mappings scoped to the account.
        account_id: Account to compute for.
        currency: Cash currency.

    Returns:
        Frozen cash-balance view.
    """
    logger.info("Computing cash balance for %s %s", account_id, currency)
    return CashBalance(
        account_id=account_id,
        currency=currency,
        settled=settled_balance(entries, account_id, currency),
        unsettled=unsettled_balance(entries, account_id, currency),
        accrued_income=accrued_income(entries, account_id, currency),
        accrued_cost=accrued_cost(entries, account_id, currency),
    )


def all_account_balances(
    entries: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str], Decimal]:
    """Rebuild every account/currency signed balance from ordered legs.

    Thin pass-through to the canonical rebuild in :mod:`postings` so callers
    consuming the cash view have one balances entry point.

    Args:
        entries: Ordered leg mappings.

    Returns:
        Mapping of ``(account_id, currency)`` to signed balance.
    """
    return recompute_balances(entries)


__all__: tuple[str, ...] = (
    "CashBalance",
    "accrued_cost",
    "accrued_income",
    "all_account_balances",
    "cash_balance",
    "settled_balance",
    "unsettled_balance",
)
