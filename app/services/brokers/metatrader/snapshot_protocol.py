"""Authenticated wire protocol used by the tested HaruQuant MT5 bridge EA."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from types import MappingProxyType

_WIRE_PROTOCOL = "haruquant.mt5.snapshot.v2"
_SOURCE_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
_MAX_SYMBOLS = 1_000
_MAX_SYMBOL_LENGTH = 64
_MAX_INTERVAL_SECONDS = 3_600
_MAX_DIGITS = 16


def parse_snapshot_frame(frame: bytes) -> Mapping[str, object]:
    """Parse one strict hello or snapshot NDJSON frame.

    Args:
        frame: One complete UTF-8 JSON frame without its newline.

    Returns:
        Immutable normalized wire-message mapping.

    Raises:
        TypeError: If a decoded field has an invalid type.
        ValueError: If the frame violates the tested EA protocol.
    """
    try:
        payload = json.loads(
            frame.decode("utf-8"),
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("invalid strict snapshot JSON") from error
    if not isinstance(payload, dict):
        raise TypeError("protocol message must be an object")
    if payload.get("protocol") != _WIRE_PROTOCOL:
        raise ValueError("unsupported snapshot protocol")
    message_type = payload.get("type")
    if message_type == "hello":
        return _parse_hello(payload)
    if message_type == "snapshot":
        return _parse_snapshot(payload)
    if message_type == "symbols_applied":
        return _parse_symbols_applied(payload)
    if message_type == "heartbeat":
        return _parse_heartbeat(payload)
    raise ValueError("unsupported snapshot message type")


def build_set_symbols_frame(revision: int, symbols: tuple[str, ...]) -> bytes:
    """Serialize one complete desired-symbol command as NDJSON.

    Args:
        revision: Positive monotonic desired-set revision.
        symbols: Exact unique broker-native symbols, possibly empty.

    Returns:
        UTF-8 newline-terminated command frame.

    Raises:
        TypeError: If a value has an invalid type.
        ValueError: If a value violates protocol bounds.
    """
    if revision <= 0:
        raise ValueError("symbol revision must be positive")
    normalized = _symbols(symbols, allow_empty=True)
    payload = {
        "type": "set_symbols",
        "protocol": _WIRE_PROTOCOL,
        "revision": revision,
        "symbols": normalized,
    }
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def _reject_constant(_value: str) -> None:
    """Reject non-standard JSON numeric constants.

    Args:
        _value: Invalid JSON constant.

    Raises:
        ValueError: Always.
    """
    raise ValueError("non-standard JSON constant is forbidden")


def _parse_hello(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Validate the first authenticated connection message.

    Args:
        payload: Decoded hello object.

    Returns:
        Immutable normalized hello.

    Raises:
        TypeError: If a field has an invalid type.
        ValueError: If a field violates protocol bounds.
    """
    _require_exact_keys(
        payload,
        {"type", "protocol", "source_id", "token", "interval_seconds", "symbols"},
    )
    source_id = _text(payload.get("source_id"), "source_id", 64)
    if _SOURCE_PATTERN.fullmatch(source_id) is None:
        raise ValueError("source_id has an invalid format")
    token = _text(payload.get("token"), "token", 512)
    interval = _integer(payload.get("interval_seconds"), "interval_seconds")
    if not 1 <= interval <= _MAX_INTERVAL_SECONDS:
        raise ValueError("interval_seconds is outside bounds")
    raw_symbols = payload.get("symbols")
    symbols = _symbols(raw_symbols, allow_empty=True)
    return MappingProxyType(
        {
            "type": "hello",
            "protocol": _WIRE_PROTOCOL,
            "source_id": source_id,
            "token": token,
            "interval_seconds": interval,
            "symbols": symbols,
        }
    )


def _parse_snapshot(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Validate one latest-value multi-symbol snapshot.

    Args:
        payload: Decoded snapshot object.

    Returns:
        Immutable normalized snapshot.

    Raises:
        TypeError: If a field has an invalid type.
        ValueError: If a field violates protocol bounds.
    """
    _require_exact_keys(
        payload,
        {"type", "protocol", "sequence", "revision", "quotes", "errors"},
    )
    sequence = _integer(payload.get("sequence"), "sequence")
    revision = _integer(payload.get("revision"), "revision")
    if sequence <= 0:
        raise ValueError("snapshot sequence must be positive")
    if revision <= 0:
        raise ValueError("snapshot revision must be positive")
    raw_quotes = payload.get("quotes")
    raw_errors = payload.get("errors")
    if not isinstance(raw_quotes, list) or len(raw_quotes) > _MAX_SYMBOLS:
        raise TypeError("quotes must be a bounded array")
    if not isinstance(raw_errors, list) or len(raw_errors) > _MAX_SYMBOLS:
        raise TypeError("errors must be a bounded array")
    quotes = tuple(_parse_quote(value) for value in raw_quotes)
    errors = tuple(_parse_symbol_error(value) for value in raw_errors)
    quote_symbols = tuple(str(value["symbol"]) for value in quotes)
    error_symbols = tuple(str(value["symbol"]) for value in errors)
    if len(quote_symbols) != len(set(quote_symbols)):
        raise ValueError("quote symbols must be unique")
    if len(error_symbols) != len(set(error_symbols)):
        raise ValueError("error symbols must be unique")
    if set(quote_symbols) & set(error_symbols):
        raise ValueError("a symbol cannot be both quote and error")
    return MappingProxyType(
        {
            "type": "snapshot",
            "protocol": _WIRE_PROTOCOL,
            "sequence": sequence,
            "revision": revision,
            "quotes": quotes,
            "errors": errors,
        }
    )


def _parse_symbols_applied(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Validate one EA acknowledgment of a complete desired symbol set.

    Args:
        payload: Decoded protocol payload.

    Returns:
        Immutable normalized acknowledgment.

    Raises:
        TypeError: If a field has an invalid type.
        ValueError: If a field violates protocol bounds.
    """
    _require_exact_keys(
        payload,
        {"type", "protocol", "revision", "symbols", "errors"},
    )
    revision = _integer(payload.get("revision"), "revision")
    if revision <= 0:
        raise ValueError("symbol revision must be positive")
    symbols = _symbols(payload.get("symbols"), allow_empty=True)
    raw_errors = payload.get("errors")
    if not isinstance(raw_errors, list) or len(raw_errors) > _MAX_SYMBOLS:
        raise TypeError("errors must be a bounded array")
    errors = tuple(_parse_symbol_error(value) for value in raw_errors)
    error_symbols = tuple(str(value["symbol"]) for value in errors)
    if len(error_symbols) != len(set(error_symbols)):
        raise ValueError("error symbols must be unique")
    if set(symbols) & set(error_symbols):
        raise ValueError("an applied symbol cannot also be rejected")
    return MappingProxyType(
        {
            "type": "symbols_applied",
            "protocol": _WIRE_PROTOCOL,
            "revision": revision,
            "symbols": symbols,
            "errors": errors,
        }
    )


def _parse_heartbeat(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Validate one idle control-channel heartbeat.

    Args:
        payload: Decoded heartbeat object.

    Returns:
        Immutable normalized heartbeat.

    Raises:
        TypeError: If the revision has an invalid type.
        ValueError: If fields or the revision violate the contract.
    """
    _require_exact_keys(payload, {"type", "protocol", "revision"})
    revision = _integer(payload.get("revision"), "revision")
    if revision <= 0:
        raise ValueError("heartbeat revision must be positive")
    return MappingProxyType(
        {
            "type": "heartbeat",
            "protocol": _WIRE_PROTOCOL,
            "revision": revision,
        }
    )


def _symbols(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    """Validate one bounded unique symbol array.

    Args:
        value: Raw decoded symbol array.
        allow_empty: Whether an empty array is valid.

    Returns:
        Normalized symbol tuple.

    Raises:
        TypeError: If the value is not a bounded array.
        ValueError: If symbols are invalid or duplicated.
    """
    minimum = 0 if allow_empty else 1
    if not isinstance(value, (list, tuple)) or not (
        minimum <= len(value) <= _MAX_SYMBOLS
    ):
        raise TypeError("symbols must be a bounded array")
    symbols = tuple(_text(item, "symbol", _MAX_SYMBOL_LENGTH) for item in value)
    if any(character in symbol for symbol in symbols for character in ('"', "\\", ",")):
        raise ValueError("symbol contains a wire-reserved character")
    if len(symbols) != len(set(symbols)):
        raise ValueError("symbols must be unique")
    return symbols


def _parse_quote(value: object) -> Mapping[str, object]:
    """Normalize one quote from the EA.

    Args:
        value: Decoded quote candidate.

    Returns:
        Immutable quote mapping.

    Raises:
        TypeError: If the quote is not an object.
        ValueError: If a quote field violates its bound.
    """
    if not isinstance(value, dict):
        raise TypeError("quote must be an object")
    _require_exact_keys(
        value,
        {
            "symbol",
            "bid",
            "ask",
            "last",
            "volume",
            "volume_real",
            "time_msc",
            "flags",
            "digits",
        },
    )
    symbol = _text(value.get("symbol"), "symbol", _MAX_SYMBOL_LENGTH)
    bid = _decimal(value.get("bid"), "bid")
    ask = _decimal(value.get("ask"), "ask")
    last = _decimal(value.get("last"), "last")
    volume = _integer(value.get("volume"), "volume")
    volume_real = _decimal(value.get("volume_real"), "volume_real")
    time_msc = _integer(value.get("time_msc"), "time_msc")
    flags = _integer(value.get("flags"), "flags")
    digits = _integer(value.get("digits"), "digits")
    if bid <= 0 or ask < bid or last < 0 or volume < 0 or volume_real < 0:
        raise ValueError("quote prices or volumes are inconsistent")
    if time_msc <= 0 or flags < 0 or not 0 <= digits <= _MAX_DIGITS:
        raise ValueError("quote metadata is outside bounds")
    return MappingProxyType(
        {
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "last": None if last == 0 else last,
            "volume": volume,
            "volume_real": volume_real,
            "time_msc": time_msc,
            "flags": flags,
            "digits": digits,
        }
    )


def _parse_symbol_error(value: object) -> Mapping[str, object]:
    """Normalize one explicit symbol-read error.

    Args:
        value: Decoded error candidate.

    Returns:
        Immutable error mapping.

    Raises:
        TypeError: If the error is not an object.
        ValueError: If a field violates its bound.
    """
    if not isinstance(value, dict):
        raise TypeError("symbol error must be an object")
    _require_exact_keys(value, {"symbol", "code"})
    return MappingProxyType(
        {
            "symbol": _text(value.get("symbol"), "symbol", _MAX_SYMBOL_LENGTH),
            "code": _integer(value.get("code"), "code"),
        }
    )


def _require_exact_keys(payload: Mapping[str, object], expected: set[str]) -> None:
    """Reject missing or extension fields.

    Args:
        payload: Decoded object.
        expected: Exact accepted key set.

    Raises:
        ValueError: If keys differ.
    """
    if set(payload) != expected:
        raise ValueError("protocol message fields do not match the contract")


def _text(value: object, field: str, maximum: int) -> str:
    """Validate one trimmed bounded string.

    Args:
        value: Decoded string candidate.
        field: Safe field label.
        maximum: Maximum accepted characters.

    Returns:
        Validated string.

    Raises:
        TypeError: If the value is not text.
        ValueError: If the value is empty, untrimmed, or oversized.
    """
    if not isinstance(value, str):
        raise TypeError("protocol text field has an invalid type")
    if not value or value != value.strip() or len(value) > maximum:
        message = f"{field} is outside text bounds"
        raise ValueError(message)
    return value


def _integer(value: object, field: str) -> int:
    """Validate one integer without boolean coercion.

    Args:
        value: Decoded integer candidate.
        field: Safe field label.

    Returns:
        Validated integer.

    Raises:
        TypeError: If the value is not an integer.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        message = f"{field} must be an integer"
        raise TypeError(message)
    return value


def _decimal(value: object, field: str) -> Decimal:
    """Validate one finite decimal.

    Args:
        value: Decoded numeric candidate.
        field: Safe field label.

    Returns:
        Finite decimal.

    Raises:
        TypeError: If the value is not numeric.
        ValueError: If the value is invalid or non-finite.
    """
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        message = f"{field} must be numeric"
        raise TypeError(message)
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("protocol decimal is invalid") from error
    if not parsed.is_finite():
        raise ValueError("protocol decimal must be finite")
    return parsed


__all__: list[str] = []
