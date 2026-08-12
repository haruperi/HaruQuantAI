"""UI/API-owned watchlist persistence and business logic.

A watchlist is an account-owned named, ordered collection of broker symbols.
Every account has exactly one default watchlist (seeded on first read with a
curated symbol set) and may create additional named watchlists. The Markets
widget reads the default watchlist's symbols for its initial view; the
Watchlist widget lists, creates, renames, reorders, and deletes watchlists
and their items.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Final, Self

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.api.identity.errors import IdentityError
from app.services.api.persistence import (
    create_watchlist_items,
    create_watchlist_record,
    delete_watchlist_record,
    read_watchlist_items,
    read_watchlist_items_for_account,
    read_watchlist_record,
    read_watchlists_for_account,
    rename_watchlist_record,
    replace_watchlist_items_record,
    set_default_watchlist_record,
)
from app.utils import derive_stable_id, get_logger, utc_now

logger = get_logger(__name__)

_MAX_WATCHLISTS_PER_ACCOUNT: Final = 20
_MAX_ITEMS_PER_WATCHLIST: Final = 200
_MAX_NAME_LENGTH: Final = 64
_DEFAULT_WATCHLIST_NAME: Final = "default"

# Curated seed content for every account's initial "default" watchlist, in
# the exact broker-native symbols the operator trades. Grouped by asset class
# for readability; display order follows this tuple's order. The owning
# `source_id` is resolved by the caller (composition layer) at seed time, not
# hardcoded here, so the seed still applies if the active runtime broker
# ever changes.
DEFAULT_WATCHLIST_SYMBOLS: Final[tuple[str, ...]] = (
    # Forex majors + minors (28)
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY",
    "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD",
    "EURUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCHF", "USDCAD", "USDJPY",
    # Commodities (14)
    "XAUUSD", "XAUEUR", "XAUGBP", "XAUJPY", "XAUAUD", "XAUCHF", "XAGUSD",
    "XPDUSD", "XPTUSD", "Copper", "SpotBrent", "SpotCrude", "NatGas",
    "Gasoline",
    # Indices (9)
    "US500", "US30", "UK100", "GER40", "NAS100", "JPN225", "USDX", "EURX",
    "JPYX",
    # Stocks (2)
    "AMZN.US-24", "AAPL.US-24",
    # Crypto (3)
    "BTCUSD", "ETHUSD", "LTCUSD",
)  # fmt: skip


class WatchlistItem(BaseModel):
    """One symbol entry within a watchlist."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    symbol: str
    sort_order: int


class Watchlist(BaseModel):
    """One account-owned named, ordered collection of watched symbols."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    watchlist_id: str
    account_id: str
    name: str
    is_default: bool
    sort_order: int
    items: tuple[WatchlistItem, ...]
    created_at: datetime
    updated_at: datetime

    @field_validator("watchlist_id", "account_id", "name")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required trimmed text field.

        Returns:
            Validated text.

        Raises:
            ValueError: If the value is empty or padded.
        """
        if not value or value != value.strip():
            raise ValueError("watchlist text fields must be non-empty and trimmed")
        return value

    @classmethod
    def from_row(
        cls, row: Mapping[str, object], items: tuple[WatchlistItem, ...]
    ) -> Self:
        """Build one watchlist from a persisted row and its item rows.

        Args:
            row: Normalized watchlist persistence row.
            items: Pre-grouped item rows owned by this watchlist.

        Returns:
            Validated watchlist.
        """
        return cls(
            watchlist_id=str(row["watchlist_id"]),
            account_id=str(row["account_id"]),
            name=str(row["name"]),
            is_default=bool(row["is_default"]),
            sort_order=int(str(row["sort_order"])),
            items=items,
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )


def _validate_name(name: str) -> str:
    """Validate one bounded trimmed watchlist name.

    Returns:
        Trimmed watchlist name.

    Raises:
        ValueError: If the name is empty, padded, or oversized.
    """
    trimmed = name.strip()
    if not trimmed or trimmed != name:
        raise ValueError("watchlist name must be non-empty and trimmed")
    if len(trimmed) > _MAX_NAME_LENGTH:
        raise ValueError("watchlist name exceeds maximum length")
    return trimmed


def _validate_symbols(symbols: tuple[str, ...]) -> tuple[str, ...]:
    """Validate a bounded, deduplicated, trimmed symbol list.

    Returns:
        Validated symbol tuple, in the caller's order.

    Raises:
        ValueError: If the list is oversized, empty entries, or duplicated.
    """
    if len(symbols) > _MAX_ITEMS_PER_WATCHLIST:
        raise ValueError("watchlist item count exceeds maximum")
    cleaned: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        trimmed = symbol.strip()
        if not trimmed or trimmed != symbol:
            raise ValueError("symbol must be non-empty and trimmed")
        if trimmed in seen:
            raise ValueError("duplicate symbol in watchlist")
        seen.add(trimmed)
        cleaned.append(trimmed)
    return tuple(cleaned)


def _group_items_by_watchlist(
    rows: tuple[Mapping[str, object], ...],
) -> dict[str, list[WatchlistItem]]:
    """Group flat item rows by their owning watchlist id.

    Args:
        rows: Normalized item rows across one or more watchlists.

    Returns:
        Mapping of watchlist id to its ordered items.
    """
    grouped: dict[str, list[WatchlistItem]] = {}
    for row in rows:
        grouped.setdefault(str(row["watchlist_id"]), []).append(
            WatchlistItem(
                source_id=str(row["source_id"]),
                symbol=str(row["symbol"]),
                sort_order=int(str(row["sort_order"])),
            )
        )
    return grouped


def _watchlist_id_for(account_id: str, name: str) -> str:
    """Derive one stable watchlist id from its owning account and name.

    Deterministic on ``(account_id, name)`` — the same pair the database's
    uniqueness constraint already enforces — so seeding is naturally
    idempotent and no separate uniqueness probe is required.

    Args:
        account_id: Owning account identifier.
        name: Watchlist display name.

    Returns:
        Stable derived watchlist identifier.
    """
    return derive_stable_id("id", f"watchlist:{account_id}:{name}")


def _ensure_default_watchlist(
    account_id: str, *, source_id: str, request_id: str
) -> None:
    """Idempotently seed the account's default watchlist if none exists yet.

    Args:
        account_id: Owning account identifier.
        source_id: Data source identifier the seeded items belong to.
        request_id: Canonical operation request identifier.
    """
    watchlist_id = _watchlist_id_for(account_id, _DEFAULT_WATCHLIST_NAME)
    now = utc_now().isoformat()
    created = create_watchlist_record(
        watchlist_id=watchlist_id,
        account_id=account_id,
        name=_DEFAULT_WATCHLIST_NAME,
        is_default=True,
        sort_order=0,
        created_at=now,
        request_id=request_id,
    )
    if created == 0:
        return
    logger.info("Seeded default watchlist for account")
    items = tuple(
        (source_id, symbol, index)
        for index, symbol in enumerate(DEFAULT_WATCHLIST_SYMBOLS)
    )
    create_watchlist_items(
        watchlist_id=watchlist_id,
        items=items,
        created_at=now,
        request_id=request_id,
    )


def list_watchlists(
    account_id: str, *, source_id: str, request_id: str
) -> tuple[Watchlist, ...]:
    """List every watchlist owned by one account, seeding the default first.

    Args:
        account_id: Owning account identifier.
        source_id: Data source identifier used only if seeding is required.
        request_id: Canonical operation request identifier.

    Returns:
        The account's watchlists, ordered for display.
    """
    watchlist_rows = read_watchlists_for_account(account_id, request_id=request_id)
    if not watchlist_rows:
        _ensure_default_watchlist(
            account_id, source_id=source_id, request_id=request_id
        )
        watchlist_rows = read_watchlists_for_account(account_id, request_id=request_id)
    item_rows = read_watchlist_items_for_account(account_id, request_id=request_id)
    grouped = _group_items_by_watchlist(item_rows)
    return tuple(
        Watchlist.from_row(row, tuple(grouped.get(str(row["watchlist_id"]), [])))
        for row in watchlist_rows
    )


def get_watchlist(watchlist_id: str, account_id: str, *, request_id: str) -> Watchlist:
    """Read one watchlist, scoped to the owning account.

    Args:
        watchlist_id: Stable watchlist identifier.
        account_id: Owning account identifier.
        request_id: Canonical operation request identifier.

    Returns:
        The watchlist with its current items.

    Raises:
        IdentityError: If the watchlist is not found or not owned.
    """
    rows = read_watchlist_record(watchlist_id, request_id=request_id)
    if not rows or str(rows[0]["account_id"]) != account_id:
        raise IdentityError("WATCHLIST_NOT_FOUND")
    item_rows = read_watchlist_items(watchlist_id, request_id=request_id)
    return Watchlist.from_row(rows[0], _items_from_rows(item_rows))


def create_watchlist(account_id: str, name: str, *, request_id: str) -> Watchlist:
    """Create one new empty, non-default watchlist for an account.

    Args:
        account_id: Owning account identifier.
        name: Requested display name, unique per account.
        request_id: Canonical operation request identifier.

    Returns:
        The newly created empty watchlist.

    Raises:
        IdentityError: If the account is at its watchlist limit or the name
            is already taken.
    """
    validated_name = _validate_name(name)
    existing = read_watchlists_for_account(account_id, request_id=request_id)
    if len(existing) >= _MAX_WATCHLISTS_PER_ACCOUNT:
        raise IdentityError("WATCHLIST_LIMIT_EXCEEDED")
    watchlist_id = _watchlist_id_for(account_id, validated_name)
    now = utc_now().isoformat()
    affected = create_watchlist_record(
        watchlist_id=watchlist_id,
        account_id=account_id,
        name=validated_name,
        is_default=False,
        sort_order=len(existing),
        created_at=now,
        request_id=request_id,
    )
    if affected == 0:
        raise IdentityError("WATCHLIST_NAME_CONFLICT")
    rows = read_watchlist_record(watchlist_id, request_id=request_id)
    return Watchlist.from_row(rows[0], ())


def rename_watchlist(
    watchlist_id: str, account_id: str, name: str, *, request_id: str
) -> Watchlist:
    """Rename one watchlist owned by the given account.

    Args:
        watchlist_id: Stable watchlist identifier.
        account_id: Owning account identifier.
        name: New display name, unique per account.
        request_id: Canonical operation request identifier.

    Returns:
        The renamed watchlist with its current items.

    Raises:
        IdentityError: If the watchlist is not found, not owned, or the name
            is already taken.
    """
    validated_name = _validate_name(name)
    now = utc_now().isoformat()
    affected = rename_watchlist_record(
        watchlist_id=watchlist_id,
        account_id=account_id,
        name=validated_name,
        updated_at=now,
        request_id=request_id,
    )
    if affected == 0:
        raise IdentityError("WATCHLIST_NOT_FOUND")
    return get_watchlist(watchlist_id, account_id, request_id=request_id)


def set_default_watchlist(
    watchlist_id: str, account_id: str, *, request_id: str
) -> Watchlist:
    """Move the account's default flag to the given watchlist.

    Args:
        watchlist_id: Watchlist to become the account's default.
        account_id: Owning account identifier.
        request_id: Canonical operation request identifier.

    Returns:
        The now-default watchlist with its current items.

    Raises:
        IdentityError: If the watchlist is not found or not owned.
    """
    now = utc_now().isoformat()
    affected = set_default_watchlist_record(
        account_id=account_id,
        watchlist_id=watchlist_id,
        updated_at=now,
        request_id=request_id,
    )
    if affected == 0:
        raise IdentityError("WATCHLIST_NOT_FOUND")
    return get_watchlist(watchlist_id, account_id, request_id=request_id)


def replace_watchlist_items(
    watchlist_id: str,
    account_id: str,
    symbols: tuple[str, ...],
    *,
    source_id: str,
    request_id: str,
) -> Watchlist:
    """Replace one watchlist's complete, ordered symbol list.

    Args:
        watchlist_id: Stable watchlist identifier.
        account_id: Owning account identifier.
        symbols: Complete replacement symbol list, in display order.
        source_id: Data source identifier the new items belong to.
        request_id: Canonical operation request identifier.

    Returns:
        The watchlist with its replaced items.

    Raises:
        IdentityError: If the watchlist is not found or not owned.
    """
    validated_symbols = _validate_symbols(symbols)
    now = utc_now().isoformat()
    items = tuple(
        (source_id, symbol, index) for index, symbol in enumerate(validated_symbols)
    )
    # Ownership is checked by the following read, not this statement's
    # affected-row count: an empty replacement legitimately reports 0 rows
    # inserted even when the watchlist exists and is owned.
    replace_watchlist_items_record(
        watchlist_id=watchlist_id,
        account_id=account_id,
        items=items,
        updated_at=now,
        request_id=request_id,
    )
    return get_watchlist(watchlist_id, account_id, request_id=request_id)


def delete_watchlist(watchlist_id: str, account_id: str, *, request_id: str) -> None:
    """Delete one non-default watchlist owned by the given account.

    Args:
        watchlist_id: Stable watchlist identifier.
        account_id: Owning account identifier.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If the watchlist is not found, not owned, or is the
            account's current default (reassign the default first).
    """
    rows = read_watchlist_record(watchlist_id, request_id=request_id)
    if not rows or str(rows[0]["account_id"]) != account_id:
        raise IdentityError("WATCHLIST_NOT_FOUND")
    if bool(rows[0]["is_default"]):
        raise IdentityError("WATCHLIST_DEFAULT_UNDELETABLE")
    affected = delete_watchlist_record(
        watchlist_id=watchlist_id, account_id=account_id, request_id=request_id
    )
    if affected == 0:
        raise IdentityError("WATCHLIST_NOT_FOUND")


def _items_from_rows(
    rows: tuple[Mapping[str, object], ...],
) -> tuple[WatchlistItem, ...]:
    """Project raw item rows into validated, ordered watchlist items.

    Args:
        rows: Normalized item rows for one watchlist.

    Returns:
        Validated items in persisted order.
    """
    return tuple(
        WatchlistItem(
            source_id=str(row["source_id"]),
            symbol=str(row["symbol"]),
            sort_order=int(str(row["sort_order"])),
        )
        for row in rows
    )


__all__ = (
    "DEFAULT_WATCHLIST_SYMBOLS",
    "Watchlist",
    "WatchlistItem",
    "create_watchlist",
    "delete_watchlist",
    "get_watchlist",
    "list_watchlists",
    "rename_watchlist",
    "replace_watchlist_items",
    "set_default_watchlist",
)
