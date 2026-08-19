"""Account-watchlist orchestration and persistence delegation.

A watchlist is an account-owned named, ordered collection of broker symbols.
Every account has exactly one default watchlist (seeded on first read with a
curated symbol set) and may create additional named watchlists. The Markets
widget reads the default watchlist's symbols for its initial view; the
Watchlist widget lists, creates, renames, reorders, and deletes watchlists
and their items.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from app.services.api.identity.errors import IdentityError
from app.services.api.widgets.markets.orchestration import resolve_runtime_source_id
from app.services.api.widgets.watchlists.persistence import (
    create_watchlist_items,
    create_watchlist_record,
    delete_watchlist_record,
    read_watchlist_items,
    read_watchlist_items_for_account,
    read_watchlist_record,
    read_watchlists_for_account,
    rename_watchlist_record,
    reorder_watchlists_record,
    replace_watchlist_items_record,
    set_default_watchlist_record,
)
from app.services.api.widgets.watchlists.schemas import Watchlist, WatchlistItem
from app.services.data import (
    build_symbol_metadata_request,
    classify_symbol,
    get_symbol_metadata,
)
from app.utils import derive_stable_id, get_logger, utc_now

logger = get_logger(__name__)

_MAX_WATCHLISTS_PER_ACCOUNT: Final = 20
_MAX_ITEMS_PER_WATCHLIST: Final = 200
_MAX_NAME_LENGTH: Final = 64
_DEFAULT_WATCHLIST_NAME: Final = "default"
_UNAVAILABLE_METADATA_VALUE: Final = "Attribute is not available with this broker."

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


def list_runtime_watchlists(
    account_id: str, *, request_id: str
) -> tuple[Watchlist, ...]:
    """List watchlists using the fail-closed configured runtime source.

    Args:
        account_id: Authenticated account identity.
        request_id: Canonical request identifier.

    Returns:
        Account-owned watchlists in display order.
    """
    source_id = resolve_runtime_source_id(None, request_id=request_id)
    watchlists = list_watchlists(account_id, source_id=source_id, request_id=request_id)
    persisted_items = read_watchlist_items_for_account(
        account_id, request_id=request_id
    )
    empty_classes_by_watchlist: dict[str, set[str]] = {}
    for row in persisted_items:
        if str(row.get("asset_class") or "").strip():
            continue
        empty_classes_by_watchlist.setdefault(str(row["watchlist_id"]), set()).add(
            str(row["symbol"])
        )
    return tuple(
        _reconcile_runtime_asset_classes(
            watchlist,
            source_id=source_id,
            request_id=request_id,
            empty_class_symbols=frozenset(
                empty_classes_by_watchlist.get(watchlist.watchlist_id, set())
            ),
        )
        for watchlist in watchlists
    )


def update_watchlist(
    watchlist_id: str,
    account_id: str,
    *,
    name: str | None,
    symbols: tuple[str, ...] | None,
    is_default: bool | None,
    sort_order: int | None = None,
    request_id: str,
) -> Watchlist:
    """Apply the independently optional watchlist update operations in order.

    Args:
        watchlist_id: Target watchlist identity.
        account_id: Authenticated owning account.
        name: Optional replacement name.
        symbols: Optional replacement ordered symbols.
        is_default: Whether to promote the watchlist to default.
        sort_order: Optional replacement display order position.
        request_id: Canonical request identifier.

    Returns:
        Updated account-owned watchlist.
    """
    current = get_watchlist(watchlist_id, account_id, request_id=request_id)
    if name is not None:
        current = rename_watchlist(
            watchlist_id, account_id, name, request_id=request_id
        )
    if sort_order is not None:
        current = reorder_watchlist(
            watchlist_id, account_id, sort_order, request_id=request_id
        )
    if symbols is not None:
        source_id = resolve_runtime_source_id(None, request_id=request_id)
        asset_classes = _resolve_runtime_asset_classes(
            current,
            symbols,
            source_id=source_id,
            request_id=request_id,
        )
        current = _replace_watchlist_items(
            watchlist_id,
            account_id,
            symbols,
            source_id=source_id,
            request_id=request_id,
            asset_classes=asset_classes,
        )
    if is_default:
        current = set_default_watchlist(watchlist_id, account_id, request_id=request_id)
    return current


def _metadata_text(value: object) -> str | None:
    """Return usable broker metadata text or explicit missingness.

    Args:
        value: Normalized metadata field value.

    Returns:
        Trimmed metadata text, or ``None`` when the provider omitted it.
    """
    text = str(value or "").strip()
    if not text or text == _UNAVAILABLE_METADATA_VALUE:
        return None
    return text


def _resolve_runtime_asset_classes(
    current: Watchlist,
    symbols: tuple[str, ...],
    *,
    source_id: str,
    request_id: str,
) -> dict[str, str]:
    """Resolve classes for new symbols from exact runtime broker metadata.

    Existing persisted classifications are retained so reorder and removal do
    not introduce unnecessary external reads. Every newly added symbol must
    have readable, classifiable metadata from the connected source.

    Args:
        current: Watchlist state before the requested replacement.
        symbols: Complete requested symbol order.
        source_id: Active runtime Data source identifier.
        request_id: Canonical request identifier.

    Returns:
        Complete symbol-to-class mapping for the replacement.

    Raises:
        IdentityError: If metadata for a newly added symbol is unavailable or
            cannot be classified from the broker-owned metadata.
    """
    resolved = {
        item.symbol: item.asset_class
        for item in current.items
        if item.source_id == source_id and item.asset_class.strip()
    }
    for symbol in symbols:
        if symbol in resolved:
            continue
        asset_class = _read_runtime_asset_class(
            symbol,
            source_id=source_id,
            request_id=request_id,
        )
        if asset_class == "Other":
            logger.error("Watchlist symbol class is unavailable")
            raise IdentityError("WATCHLIST_SYMBOL_CLASS_UNAVAILABLE")
        resolved[symbol] = asset_class
    return {symbol: resolved[symbol] for symbol in symbols}


def _read_runtime_asset_class(symbol: str, *, source_id: str, request_id: str) -> str:
    """Read and classify one exact symbol from the runtime source.

    Args:
        symbol: Exact provider-native symbol.
        source_id: Active runtime Data source identifier.
        request_id: Canonical request identifier.

    Returns:
        Normalized display asset class, including the legitimate ``Other``
        catch-all when the source metadata remains inconclusive.

    Raises:
        IdentityError: If source metadata is unavailable.
    """
    response = get_symbol_metadata(
        build_symbol_metadata_request(
            source_id=source_id,
            symbol=symbol,
            request_id=request_id,
        )
    )
    metadata = response.data
    if response.status != "success" or metadata is None:
        logger.error("Watchlist symbol metadata is unavailable")
        raise IdentityError("WATCHLIST_SYMBOL_METADATA_UNAVAILABLE")
    return classify_symbol(
        _metadata_text(metadata.path),
        symbol=symbol,
        currency_base=_metadata_text(metadata.currency_base) or metadata.base_currency,
        currency_profit=(
            _metadata_text(metadata.currency_profit) or metadata.quote_currency
        ),
    )


def _reconcile_runtime_asset_classes(
    watchlist: Watchlist,
    *,
    source_id: str,
    request_id: str,
    empty_class_symbols: frozenset[str],
) -> Watchlist:
    """Persist source-derived corrections for legacy item classes.

    Migration ``api-0008`` initialized existing rows with an empty value, while
    ``Other`` was historically produced without source metadata. A runtime list
    read rechecks both cases and atomically persists successful classifications.
    Unavailable metadata leaves the existing watchlist readable and unchanged.

    Args:
        watchlist: Persisted account watchlist projected for the caller.
        source_id: Active runtime Data source identifier.
        request_id: Canonical request identifier.
        empty_class_symbols: Symbols whose raw persisted class is empty. Their
            projected watchlist value may contain a compatibility fallback.

    Returns:
        Original watchlist when no correction is available, otherwise the
        refreshed watchlist containing persisted corrections.
    """
    if not watchlist.items or any(
        item.source_id != source_id for item in watchlist.items
    ):
        return watchlist
    asset_classes = {item.symbol: item.asset_class for item in watchlist.items}
    corrected = False
    for item in watchlist.items:
        was_empty = item.symbol in empty_class_symbols
        if not was_empty and item.asset_class != "Other":
            continue
        try:
            asset_class = _read_runtime_asset_class(
                item.symbol,
                source_id=source_id,
                request_id=request_id,
            )
        except IdentityError:
            logger.warning("Preserving ambiguous watchlist class")
            continue
        if asset_class == "Other" and not was_empty:
            continue
        asset_classes[item.symbol] = asset_class
        corrected = True
    if not corrected:
        return watchlist
    logger.info("Persisting source-derived watchlist class corrections")
    return _replace_watchlist_items(
        watchlist.watchlist_id,
        watchlist.account_id,
        tuple(item.symbol for item in watchlist.items),
        source_id=source_id,
        request_id=request_id,
        asset_classes=asset_classes,
    )


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
        symbol = str(row["symbol"])
        asset_class = str(row.get("asset_class") or "") or classify_symbol(
            None, symbol=symbol
        )
        grouped.setdefault(str(row["watchlist_id"]), []).append(
            WatchlistItem(
                source_id=str(row["source_id"]),
                symbol=symbol,
                sort_order=int(str(row["sort_order"])),
                asset_class=asset_class,
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
        (source_id, symbol, index, classify_symbol(None, symbol=symbol))
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


def reorder_watchlist(
    watchlist_id: str, account_id: str, sort_order: int, *, request_id: str
) -> Watchlist:
    """Reposition one watchlist owned by the given account.

    Args:
        watchlist_id: Target watchlist identity.
        account_id: Owning account identifier.
        sort_order: Zero-based display order position.
        request_id: Canonical operation request identifier.

    Returns:
        The updated watchlist with its current items.

    Raises:
        IdentityError: If the watchlist is not found or not owned.
        ValueError: If sort_order is negative.
    """
    if sort_order < 0:
        raise ValueError("sort_order cannot be negative")
    now = utc_now().isoformat()
    affected = reorder_watchlists_record(
        account_id=account_id,
        watchlist_id=watchlist_id,
        sort_order=sort_order,
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
    return _replace_watchlist_items(
        watchlist_id,
        account_id,
        symbols,
        source_id=source_id,
        request_id=request_id,
        asset_classes=None,
    )


def _replace_watchlist_items(
    watchlist_id: str,
    account_id: str,
    symbols: tuple[str, ...],
    *,
    source_id: str,
    request_id: str,
    asset_classes: Mapping[str, str] | None,
) -> Watchlist:
    """Persist a validated replacement with optional source-derived classes.

    Args:
        watchlist_id: Stable watchlist identifier.
        account_id: Authenticated owning account.
        symbols: Complete replacement symbol list, in display order.
        source_id: Data source identifier for the items.
        request_id: Canonical request identifier.
        asset_classes: Complete source-derived class mapping when invoked from
            the runtime API path; ``None`` preserves the public service's
            deterministic compatibility behavior.

    Returns:
        The watchlist with its replaced items.
    """
    validated_symbols = _validate_symbols(symbols)
    now = utc_now().isoformat()
    items = tuple(
        (
            source_id,
            symbol,
            index,
            (
                asset_classes[symbol]
                if asset_classes is not None
                else classify_symbol(None, symbol=symbol)
            ),
        )
        for index, symbol in enumerate(validated_symbols)
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
    items: list[WatchlistItem] = []
    for row in rows:
        symbol = str(row["symbol"])
        asset_class = str(row.get("asset_class") or "") or classify_symbol(
            None, symbol=symbol
        )
        items.append(
            WatchlistItem(
                source_id=str(row["source_id"]),
                symbol=symbol,
                sort_order=int(str(row["sort_order"])),
                asset_class=asset_class,
            )
        )
    return tuple(items)


__all__ = (
    "DEFAULT_WATCHLIST_SYMBOLS",
    "Watchlist",
    "WatchlistItem",
    "create_watchlist",
    "delete_watchlist",
    "get_watchlist",
    "list_runtime_watchlists",
    "list_watchlists",
    "rename_watchlist",
    "replace_watchlist_items",
    "set_default_watchlist",
    "update_watchlist",
)
