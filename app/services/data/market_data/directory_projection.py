"""Project governed symbol evidence into categorized directory rows."""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from typing_extensions import TypedDict

from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.market_data.asset_classifier import OTHER, classify_symbol
from app.services.data.market_data.directory_contracts import MarketDirectoryRow
from app.services.data.market_data.snapshot import MarketSnapshot, get_market_snapshot
from app.utils import get_logger

logger = get_logger(__name__)

# A completed D1 bar supplies bounded daily OHLC context without inventing a
# separate presentation-only retrieval path.
_DIRECTORY_TIMEFRAME = "D1"


class _SnapshotEvidence(TypedDict, total=False):
    """Best-effort evidence extracted from a per-symbol market snapshot."""

    last: float | None
    bid: float | None
    ask: float | None
    spread: float | None
    volume: float | None
    open: float | None
    high: float | None
    low: float | None
    close: float | None


def _to_float(value: object) -> float | None:
    """Normalize one provider numeric value.

    Args:
        value: Provider numeric, exact decimal, or unavailable value.

    Returns:
        Finite float or ``None``.
    """
    if isinstance(value, bool | str):
        return None
    if isinstance(value, Decimal):
        return float(value) if value.is_finite() else None
    if not isinstance(value, int | float):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _first_available(*values: float | None) -> float | None:
    """Return the first available numeric value.

    Args:
        *values: Values in preference order.

    Returns:
        First non-``None`` value or ``None``.
    """
    return next((value for value in values if value is not None), None)


def _first_positive_price(*values: float | None) -> float | None:
    """Return the first usable market price.

    Some OTC providers report ``last=0`` when no exchange last-trade field
    exists. Zero therefore cannot displace genuine bid or closed-bar evidence.

    Args:
        *values: Prices in preference order.

    Returns:
        First strictly positive price or ``None``.
    """
    return next((value for value in values if value is not None and value > 0), None)


def _metadata_string(metadata: Mapping[str, object], key: str) -> str | None:
    """Read one optional metadata string.

    Args:
        metadata: Normalized provider metadata.
        key: Metadata field name.

    Returns:
        Non-empty string or ``None``.
    """
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def _bar_fields(latest_bar: object | None) -> Mapping[str, object]:
    """Extract fields from one latest-bar value.

    Args:
        latest_bar: Latest canonical bar or ``None``.

    Returns:
        Bar field mapping, possibly empty.
    """
    if latest_bar is None:
        return {}
    if isinstance(latest_bar, Mapping):
        return latest_bar
    dump = getattr(latest_bar, "model_dump", None)
    if callable(dump):
        try:
            return cast("Mapping[str, object]", dump())
        except Exception:  # noqa: BLE001 - missing optional evidence degrades safely
            logger.debug("Latest bar serialization failed; treating it as missing")
            return {}
    instance_dict = getattr(latest_bar, "__dict__", None)
    return (
        cast("Mapping[str, object]", instance_dict)
        if isinstance(instance_dict, dict)
        else {}
    )


def _extract_snapshot_evidence(snapshot: MarketSnapshot) -> _SnapshotEvidence:
    """Flatten one composite market snapshot.

    Args:
        snapshot: Level-1 and latest-bar evidence.

    Returns:
        Flat optional numeric evidence.
    """
    level1 = snapshot.level1
    bar = _bar_fields(snapshot.latest_bar)
    return _SnapshotEvidence(
        last=_to_float(level1.last),
        bid=_to_float(level1.bid),
        ask=_to_float(level1.ask),
        spread=_to_float(level1.spread),
        volume=_to_float(level1.volume),
        open=_to_float(bar.get("open")),
        high=_to_float(bar.get("high")),
        low=_to_float(bar.get("low")),
        close=_to_float(bar.get("close")),
    )


def _compute_change(
    last: float | None,
    open_price: float | None,
    close: float | None,
) -> tuple[float | None, float | None]:
    """Compute change from the bounded daily open.

    Args:
        last: Current usable price.
        open_price: Latest daily open.
        close: Latest daily close fallback.

    Returns:
        Change and percentage, or explicit missing values.
    """
    reference = last if last is not None else close
    if reference is None or open_price is None or open_price == 0:
        return None, None
    change = reference - open_price
    return change, (change / open_price) * 100.0


def _build_row(
    symbol: str,
    metadata: Mapping[str, object],
    snapshot_evidence: _SnapshotEvidence | None,
    source_id: str,
) -> MarketDirectoryRow | None:
    """Build one categorized evidence row.

    Args:
        symbol: Provider-native symbol.
        metadata: Normalized symbol metadata.
        snapshot_evidence: Optional quote and OHLC evidence.
        source_id: Owning source identifier.

    Returns:
        Directory row or ``None`` when classification is unsupported.
    """
    name = (
        _metadata_string(metadata, "name")
        or _metadata_string(metadata, "description")
        or symbol
    )
    asset_class = classify_symbol(
        path=_metadata_string(metadata, "path"),
        symbol=symbol,
        currency_base=_metadata_string(metadata, "currency_base"),
        currency_profit=_metadata_string(metadata, "currency_profit"),
    )
    if asset_class == OTHER:
        return None

    digits_raw = metadata.get("digits")
    digits = (
        digits_raw
        if isinstance(digits_raw, int) and not isinstance(digits_raw, bool)
        else None
    )
    evidence: _SnapshotEvidence = snapshot_evidence or _SnapshotEvidence()
    bid = _first_positive_price(evidence.get("bid"), _to_float(metadata.get("bid")))
    ask = _first_positive_price(evidence.get("ask"), _to_float(metadata.get("ask")))
    volume = _first_available(evidence.get("volume"), _to_float(metadata.get("volume")))
    spread = _first_available(
        evidence.get("spread"),
        ask - bid if ask is not None and bid is not None else None,
    )
    open_price = evidence.get("open")
    close = evidence.get("close")
    last = _first_positive_price(
        bid,
        evidence.get("last"),
        _to_float(metadata.get("last")),
        close,
    )
    change, change_percent = _compute_change(last, open_price, close)
    return MarketDirectoryRow(
        symbol=symbol,
        name=name,
        asset_class=asset_class,
        source_id=source_id,
        digits=digits,
        last=last,
        bid=bid,
        ask=ask,
        spread=spread,
        volume=volume,
        open=open_price,
        high=evidence.get("high"),
        low=evidence.get("low"),
        close=close,
        change=change,
        change_percent=change_percent,
    )


def _fetch_symbol_metadata_raw(
    source_id: str,
    symbol: str,
    request_id: str,
) -> Mapping[str, object]:
    """Fetch one normalized symbol metadata mapping.

    Args:
        source_id: Owning source identifier.
        symbol: Provider-native symbol.
        request_id: Trace identifier.

    Returns:
        Metadata mapping.
    """
    from app.services.data.market_data.symbol_discovery import get_symbol_metadata

    response = get_symbol_metadata(
        source_id=source_id,
        symbol=symbol,
        request_id=request_id,
    )
    data: object = unwrap_data_response(
        response,
        operation="data.market_data.directory_projection.metadata",
        request_id=request_id,
    )
    dump = getattr(data, "model_dump", None)
    if callable(dump):
        return cast("Mapping[str, object]", dump())
    if isinstance(data, Mapping):
        return data
    instance_dict = getattr(data, "__dict__", None)
    return (
        cast("Mapping[str, object]", instance_dict)
        if isinstance(instance_dict, dict)
        else {}
    )


def enrich_symbols(
    source_id: str,
    symbols: tuple[str, ...],
    request_id: str,
) -> tuple[MarketDirectoryRow, ...]:
    """Enrich an ordered symbol list with governed market evidence.

    Args:
        source_id: Owning source identifier.
        symbols: Symbols in caller-declared order.
        request_id: Trace identifier.

    Returns:
        Readable, classified rows in the same order.
    """
    rows: list[MarketDirectoryRow] = []
    for symbol in symbols:
        try:
            metadata = _fetch_symbol_metadata_raw(source_id, symbol, request_id)
        except Exception:  # noqa: BLE001 - unreadable symbol is explicitly omitted
            logger.debug("Skipping symbol %s: metadata unavailable", symbol)
            continue
        snapshot_evidence: _SnapshotEvidence | None = None
        try:
            snapshot = cast(
                "MarketSnapshot",
                unwrap_data_response(
                    get_market_snapshot(
                        source_id=source_id,
                        symbol=symbol,
                        timeframe=_DIRECTORY_TIMEFRAME,
                        request_id=request_id,
                    ),
                    operation="data.market_data.directory_projection.snapshot",
                    request_id=request_id,
                ),
            )
            snapshot_evidence = _extract_snapshot_evidence(snapshot)
        except Exception:  # noqa: BLE001 - optional snapshot leg remains missing
            logger.debug("No snapshot evidence for %s", symbol)
        row = _build_row(symbol, metadata, snapshot_evidence, source_id)
        if row is not None:
            rows.append(row)
    return tuple(rows)


__all__ = ("enrich_symbols",)
