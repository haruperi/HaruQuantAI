"""Fail-closed construction of provider specification snapshots.

Maps one raw MT5 ``symbol_info`` observation plus explicit connection
identity into a typed current snapshot. Every required field must be present
and finite; missing evidence raises before any snapshot exists. No effective
bounds are invented and no static commission rate is guessed.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import fields as dataclass_fields
from dataclasses import replace
from datetime import datetime
from decimal import Decimal

from app.services.brokers.specifications.contracts import (
    EXPIRATION_MODE_FLAGS,
    ORDER_TYPE_FLAGS,
    ROLLOVER_WEEKDAYS,
    ProviderAccountPermissions,
    ProviderCostEvidenceReference,
    ProviderSpecificationSnapshot,
)
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)

_TRADE_MODE_VALUES: tuple[str, ...] = (
    "DISABLED",
    "LONGONLY",
    "SHORTONLY",
    "CLOSEONLY",
    "FULL",
)
_SWAP_MODE_VALUES: tuple[str, ...] = (
    "DISABLED",
    "POINTS",
    "CURRENCY_SYMBOL",
    "CURRENCY_MARGIN",
    "CURRENCY_DEPOSIT",
    "INTEREST_CURRENT",
    "REOPEN_CURRENT",
    "REOPEN_BID",
)
_EXECUTION_MODE_VALUES: tuple[str, ...] = (
    "REQUEST",
    "INSTANT",
    "MARKET",
    "EXCHANGE",
)
_GTC_MODE_VALUES: tuple[str, ...] = ("GTC", "DAILY", "SPECIFIED")
_CALCULATION_MODE_VALUES: tuple[str, ...] = (
    "FOREX",
    "FOREX_NO_LEVERAGE",
    "FUTURES",
    "CFD",
    "CFDINDEX",
    "CFDLEVERAGE",
    "EXCHANGES_STOCKS",
    "EXCHANGES_FUTURES",
    "EXCHANGES_FUTURES_FORTS",
    "FOREX_MARGIN",
)
_MARGIN_MODE_VALUES: Mapping[int, str] = {
    0: "NETTING",
    2: "RETAIL_HEDGING",
}


def _field(value: object, name: str) -> object:
    """Read one required raw provider field.

    Args:
        value: Raw provider record (mapping, namedtuple, or attribute object).
        name: Raw provider field name.

    Returns:
        The raw field value.

    Raises:
        ValueError: If the field is absent.
    """
    result = _optional(value, name)
    if result is None:
        message = "missing required provider specification field: " + name
        raise ValueError(message)
    return result


def _optional(value: object, name: str) -> object | None:
    """Read one optional raw provider field.

    Args:
        value: Raw provider record.
        name: Raw provider field name.

    Returns:
        The raw field value, or None when absent.
    """
    if isinstance(value, Mapping):
        return value.get(name)
    if hasattr(value, "_asdict"):
        as_dict = value._asdict
        return dict(as_dict()).get(name)
    return getattr(value, name, None)


def _decimal(value: object, name: str) -> Decimal:
    """Convert one raw numeric field to a finite Decimal.

    Binary floats are stringified before parsing, matching the established
    MT5 mapping convention.

    Args:
        value: Raw provider value.
        name: Raw provider field name.

    Returns:
        The parsed finite Decimal.

    Raises:
        ValueError: If the value is missing or not finite.
    """
    if value is None or isinstance(value, bool):
        message = "missing required provider specification field: " + name
        raise ValueError(message)
    parsed = Decimal(str(value))
    if not parsed.is_finite():
        message = "provider specification field is not finite: " + name
        raise ValueError(message)
    return parsed


def _decimal_or_none(value: object) -> Decimal | None:
    """Convert one optional raw numeric field to a Decimal when present.

    Args:
        value: Raw optional provider value.

    Returns:
        The parsed finite Decimal, or None when the value is absent.
    """
    if value is None or isinstance(value, bool):
        return None
    return Decimal(str(value))


def _int(value: object, name: str) -> int:
    """Read one required raw integer field.

    Args:
        value: Raw provider value.
        name: Raw provider field name.

    Returns:
        The parsed integer.

    Raises:
        ValueError: If the value is missing or unparsable.
    """
    if value is None or isinstance(value, bool):
        message = "missing required provider specification field: " + name
        raise ValueError(message)
    return int(str(value))


def _text(value: object, name: str) -> str:
    """Read one required raw text field.

    Args:
        value: Raw provider value.
        name: Raw provider field name.

    Returns:
        The stripped non-empty text.

    Raises:
        ValueError: If the value is missing or blank.
    """
    if value is None or not str(value).strip():
        message = "missing required provider specification field: " + name
        raise ValueError(message)
    return str(value).strip()


def _index_name(value: int, table: tuple[str, ...], name: str, unknown: str) -> str:
    """Map one raw enum index onto the verified vocabulary.

    Args:
        value: Raw provider index.
        table: Verified value table.
        name: Field name for the error message.
        unknown: Marker returned for unmapped indices.

    Returns:
        The mapped name, or ``unknown`` when the index is unmapped.

    Raises:
        ValueError: If the index is negative.
    """
    if value < 0:
        message = name + " must not be negative"
        raise ValueError(message)
    if value < len(table):
        return table[value]
    return unknown


def _flag_names(mask: int, flags: tuple[tuple[int, str], ...]) -> tuple[str, ...]:
    """Expand one verified provider bit mask into sorted mode names.

    Args:
        mask: Provider bit mask.
        flags: Verified bit-to-name pairs.

    Returns:
        Sorted tuple of admitted mode names for the set bits.
    """
    return tuple(sorted(name for bit, name in flags if mask & bit))


def _account_digest(broker: str, server: str, account_id: str) -> str:
    """Return the redacted digest binding one provider account identity.

    Args:
        broker: Broker identifier.
        server: Provider server name.
        account_id: Raw provider account identifier (never stored).

    Returns:
        Lowercase SHA-256 digest over the account identity material.
    """
    material = "brokers.account.v1|" + broker + "|" + server + "|" + account_id
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _checksum(snapshot_fields: Mapping[str, object]) -> str:
    """Return the canonical checksum over snapshot material.

    Args:
        snapshot_fields: Canonical field mapping without the checksum itself.

    Returns:
        SHA-256 digest over the canonical JSON material.
    """
    return hashlib.sha256(
        canonical_json(dict(snapshot_fields)).encode("utf-8")
    ).hexdigest()


def _json_safe(value: object) -> object:
    """Convert one snapshot value to deterministic JSON-safe material.

    Args:
        value: Snapshot field value.

    Returns:
        JSON-safe representation (strings for Decimals and datetimes,
        lists for tuples, dicts for nested contract blocks).
    """
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bool | int | str) or value is None:
        return value
    if isinstance(value, tuple | list):
        return [_json_safe(item) for item in value]
    if isinstance(value, ProviderCostEvidenceReference | ProviderAccountPermissions):
        return _block_safe(value)
    return str(value)


def _block_safe(
    value: ProviderCostEvidenceReference | ProviderAccountPermissions,
) -> dict[str, object]:
    """Serialize one nested contract block.

    Args:
        value: Cost-evidence reference or account-permission block.

    Returns:
        JSON-safe mapping of the block's fields.
    """
    if isinstance(value, ProviderCostEvidenceReference):
        return {
            "evidence_id": value.evidence_id,
            "checksum": value.checksum,
            "evidence_kind": value.evidence_kind,
        }
    return {
        "margin_mode": value.margin_mode,
        "stop_out_mode": value.stop_out_mode,
        "fifo": value.fifo,
        "hedging_permitted": value.hedging_permitted,
        "unverified": list(value.unverified),
    }


def dump_provider_specification_snapshot(
    snapshot: ProviderSpecificationSnapshot,
) -> dict[str, object]:
    """Return the canonical JSON-safe mapping of one snapshot.

    Args:
        snapshot: Snapshot to serialize.

    Returns:
        Deterministic JSON-safe field mapping including the checksum.
    """
    return {
        entry.name: _json_safe(getattr(snapshot, entry.name))
        for entry in dataclass_fields(snapshot)
    }


def parse_provider_specification_snapshot(
    value: Mapping[str, object],
) -> ProviderSpecificationSnapshot:
    """Parse one canonical snapshot mapping back into the typed contract.

    Args:
        value: JSON-safe mapping produced by ``dump_provider_specification_snapshot``.

    Returns:
        The validated immutable snapshot with a verified checksum.

    Raises:
        ValueError: If fields are missing, mistyped, the checksum does not
            match the canonical material, or effective-date fields are
            present (the snapshot is current-observation only).
    """
    if "effective_from" in value or "effective_to" in value:
        raise ValueError("provider specification snapshots carry no effective bounds")
    names = {entry.name for entry in dataclass_fields(ProviderSpecificationSnapshot)}
    if set(value) != names:
        raise ValueError("snapshot fields do not match the canonical schema")
    converted = {name: _convert_field(name, value[name]) for name in names}
    snapshot = ProviderSpecificationSnapshot(**converted)  # type: ignore[arg-type]
    if not verify_provider_specification_snapshot(snapshot):
        raise ValueError("snapshot checksum does not match the canonical material")
    return snapshot


_DECIMAL_FIELDS = frozenset(
    {
        "volume_min",
        "volume_max",
        "volume_step",
        "directional_volume_limit",
        "point",
        "tick_size",
        "tick_value",
        "tick_value_profit",
        "tick_value_loss",
        "contract_size",
        "margin_initial",
        "margin_maintenance",
        "margin_hedged",
        "swap_long",
        "swap_short",
    }
)
_TUPLE_FIELDS = frozenset(
    {"filling_modes", "order_types", "expiration_modes", "unverified"}
)


def _convert_field(name: str, raw: object) -> object:
    """Convert one dumped snapshot field back into its typed value.

    Args:
        name: Canonical field name.
        raw: JSON-safe dumped value.

    Returns:
        The typed field value for snapshot construction.
    """
    if name in _DECIMAL_FIELDS:
        return None if raw is None else Decimal(str(raw))
    if name in _TUPLE_FIELDS:
        items = raw if isinstance(raw, tuple | list) else ()
        return tuple(str(item) for item in items)
    if name == "observed_at":
        return datetime.fromisoformat(str(raw))
    if name == "account_permissions":
        return _convert_permissions(raw)
    if name == "cost_evidence":
        return _convert_cost_evidence(raw)
    return raw


def _optional_str(value: object) -> str | None:
    """Return one optional dumped value as text.

    Args:
        value: Optional dumped value.

    Returns:
        The stringified value, or None when absent.
    """
    return None if value is None else str(value)


def _convert_permissions(raw: object) -> ProviderAccountPermissions:
    """Convert one dumped account-permission block.

    Args:
        raw: Raw dumped permission block.

    Returns:
        The validated permission block.

    Raises:
        TypeError: If the dumped block is not a mapping.
    """
    if raw is None:
        return ProviderAccountPermissions(
            unverified=(
                "margin_mode",
                "stop_out_mode",
                "fifo",
                "hedging_permitted",
            )
        )
    if not isinstance(raw, Mapping):
        raise TypeError("account permission block must be a mapping")
    unverified = raw.get("unverified")
    unverified_items = unverified if isinstance(unverified, tuple | list) else ()
    return ProviderAccountPermissions(
        margin_mode=_optional_str(raw.get("margin_mode")),
        stop_out_mode=_optional_str(raw.get("stop_out_mode")),
        fifo=raw.get("fifo") if isinstance(raw.get("fifo"), bool) else None,
        hedging_permitted=(
            raw.get("hedging_permitted")
            if isinstance(raw.get("hedging_permitted"), bool)
            else None
        ),
        unverified=tuple(str(item) for item in unverified_items),
    )


def _convert_cost_evidence(raw: object) -> ProviderCostEvidenceReference | None:
    """Convert one dumped cost-evidence reference.

    Args:
        raw: Raw dumped evidence reference.

    Returns:
        The typed reference, or None when the dump carried no evidence.

    Raises:
        TypeError: If the dumped reference is not a mapping.
    """
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise TypeError("cost evidence reference must be a mapping")
    return ProviderCostEvidenceReference(
        evidence_id=str(raw["evidence_id"]),
        checksum=str(raw["checksum"]),
        evidence_kind=str(raw["evidence_kind"]),
    )


def build_provider_specification_snapshot(
    symbol_info: object,
    *,
    broker: str,
    server: str,
    account_id: str,
    environment: str,
    terminal_build: str,
    source_revision: str,
    observed_at: datetime,
    retrieval_provenance: str = "metatrader.symbol_info",
    account_info: object | None = None,
    cost_evidence_id: str | None = None,
    cost_evidence_checksum: str | None = None,
) -> ProviderSpecificationSnapshot:
    """Build one typed current provider specification snapshot.

    Args:
        symbol_info: Raw MT5 ``symbol_info`` record for one symbol.
        broker: Broker identifier (e.g. ``mt5``).
        server: Provider server name.
        account_id: Raw provider account identifier; stored only as a digest.
        environment: Broker environment (``demo``/``live``/...).
        terminal_build: Provider terminal build identifier.
        source_revision: Source revision of the observation.
        observed_at: Aware-UTC observation time.
        retrieval_provenance: Provenance label of the retrieval path.
        account_info: Optional raw MT5 ``account_info`` record for the
            account-permission block; fields the upstream contract does not
            expose stay unverified exclusions.
        cost_evidence_id: Optional separate dynamic cost-evidence identifier.
        cost_evidence_checksum: Optional checksum of the cost evidence.

    Returns:
        The validated immutable current snapshot.

    Raises:
        ValueError: If any required field is missing, non-finite, or outside
            the verified vocabulary.
    """
    filling_mask = _int(_field(symbol_info, "filling_mode"), "filling_mode")
    filling_modes = _flag_names(filling_mask, ((1, "FOK"), (2, "IOC"))) or ("RETURN",)
    order_types = _flag_names(
        _int(_field(symbol_info, "order_mode"), "order_mode"), ORDER_TYPE_FLAGS
    )
    expiration_modes = _flag_names(
        _int(_field(symbol_info, "expiration_mode"), "expiration_mode"),
        EXPIRATION_MODE_FLAGS,
    )
    gtc_mode = _index_name(
        _int(_field(symbol_info, "order_gtc_mode"), "order_gtc_mode"),
        _GTC_MODE_VALUES,
        "order_gtc_mode",
        unknown="UNKNOWN",
    )
    execution_mode = _index_name(
        _int(_field(symbol_info, "trade_exemode"), "trade_exemode"),
        _EXECUTION_MODE_VALUES,
        "trade_exemode",
        unknown="UNKNOWN",
    )
    trade_mode = _index_name(
        _int(_field(symbol_info, "trade_mode"), "trade_mode"),
        _TRADE_MODE_VALUES,
        "trade_mode",
        unknown="UNKNOWN",
    )
    calculation_mode = _index_name(
        _int(_field(symbol_info, "trade_calc_mode"), "trade_calc_mode"),
        _CALCULATION_MODE_VALUES,
        "trade_calc_mode",
        unknown="UNKNOWN",
    )
    swap_mode = _index_name(
        _int(_field(symbol_info, "swap_mode"), "swap_mode"),
        _SWAP_MODE_VALUES,
        "swap_mode",
        unknown="UNKNOWN",
    )
    rollover_index = _int(
        _field(symbol_info, "swap_rollover3days"), "swap_rollover3days"
    )
    if rollover_index < 0 or rollover_index >= len(ROLLOVER_WEEKDAYS):
        message = "swap_rollover3days is outside the verified weekday range"
        raise ValueError(message)
    permissions = _build_permissions(account_info)
    cost_evidence = _build_cost_evidence(cost_evidence_id, cost_evidence_checksum)
    provider_symbol = _text(_field(symbol_info, "name"), "name")
    fields: dict[str, object] = {
        "broker": broker,
        "server": server,
        "account_digest": _account_digest(broker, server, account_id),
        "environment": environment,
        "terminal_build": terminal_build,
        "source_revision": source_revision,
        "observed_at": observed_at,
        "retrieval_provenance": retrieval_provenance,
        "provider_symbol": provider_symbol,
        "filling_modes": filling_modes,
        "order_types": order_types,
        "expiration_modes": expiration_modes,
        "gtc_mode": gtc_mode,
        "execution_mode": execution_mode,
        "trade_mode": trade_mode,
        "calculation_mode": calculation_mode,
        "stops_level_points": _int(
            _field(symbol_info, "trade_stops_level"), "trade_stops_level"
        ),
        "freeze_level_points": _int(
            _field(symbol_info, "trade_freeze_level"), "trade_freeze_level"
        ),
        "volume_min": _decimal(_field(symbol_info, "volume_min"), "volume_min"),
        "volume_max": _decimal(_field(symbol_info, "volume_max"), "volume_max"),
        "volume_step": _decimal(_field(symbol_info, "volume_step"), "volume_step"),
        "directional_volume_limit": _decimal_or_none(
            _optional(symbol_info, "volume_limit")
        ),
        "point": _decimal(_field(symbol_info, "point"), "point"),
        "digits": _int(_field(symbol_info, "digits"), "digits"),
        "tick_size": _decimal(
            _field(symbol_info, "trade_tick_size"), "trade_tick_size"
        ),
        "tick_value": _decimal_or_none(_optional(symbol_info, "trade_tick_value")),
        "tick_value_profit": _decimal_or_none(
            _optional(symbol_info, "trade_tick_value_profit")
        ),
        "tick_value_loss": _decimal_or_none(
            _optional(symbol_info, "trade_tick_value_loss")
        ),
        "contract_size": _decimal(
            _field(symbol_info, "trade_contract_size"), "trade_contract_size"
        ),
        "base_currency": _text(_field(symbol_info, "currency_base"), "currency_base"),
        "profit_currency": _text(
            _field(symbol_info, "currency_profit"), "currency_profit"
        ),
        "margin_currency": _text(
            _field(symbol_info, "currency_margin"), "currency_margin"
        ),
        "margin_initial": _decimal_or_none(_optional(symbol_info, "margin_initial")),
        "margin_maintenance": _decimal_or_none(
            _optional(symbol_info, "margin_maintenance")
        ),
        "margin_hedged": _decimal_or_none(_optional(symbol_info, "margin_hedged")),
        "margin_hedged_use_leg": (
            None
            if _optional(symbol_info, "margin_hedged_use_leg") is None
            else bool(_optional(symbol_info, "margin_hedged_use_leg"))
        ),
        "swap_mode": swap_mode,
        "swap_long": _decimal(_field(symbol_info, "swap_long"), "swap_long"),
        "swap_short": _decimal(_field(symbol_info, "swap_short"), "swap_short"),
        "swap_rollover3days": ROLLOVER_WEEKDAYS[rollover_index],
        "account_permissions": permissions,
        "cost_evidence": cost_evidence,
    }
    base = ProviderSpecificationSnapshot(
        **fields,  # type: ignore[arg-type]
    )
    material = dump_provider_specification_snapshot(base)
    material.pop("checksum", None)
    checksum = _checksum(material)
    snapshot = replace(base, checksum=checksum)
    logger.info(
        "Built provider specification snapshot for %s/%s (calculation mode %s)",
        broker,
        provider_symbol,
        calculation_mode,
    )
    return snapshot


def verify_provider_specification_snapshot(
    snapshot: ProviderSpecificationSnapshot,
) -> bool:
    """Recompute and compare the snapshot checksum.

    Args:
        snapshot: Snapshot to verify.

    Returns:
        True when the stored checksum matches the canonical material.

    Raises:
        ValueError: If the snapshot carries no checksum.
    """
    if not snapshot.checksum:
        raise ValueError("snapshot checksum is required for verification")
    material = dump_provider_specification_snapshot(snapshot)
    material.pop("checksum", None)
    return _checksum(material) == snapshot.checksum


def _build_permissions(account_info: object | None) -> ProviderAccountPermissions:
    """Build the account-permission block from optional raw account evidence.

    The upstream ``account_info`` contract exposes ``margin_mode``; stop-out
    policy and FIFO discipline are not exposed and remain explicit
    unverified exclusions.

    Args:
        account_info: Raw MT5 ``account_info`` record or None.

    Returns:
        The validated permission block.

    Raises:
        ValueError: If a present field is outside the verified vocabulary.
    """
    if account_info is None:
        return ProviderAccountPermissions(
            unverified=(
                "margin_mode",
                "stop_out_mode",
                "fifo",
                "hedging_permitted",
            )
        )
    raw_mode = _optional(account_info, "margin_mode")
    margin_mode = (
        None
        if raw_mode is None
        else _MARGIN_MODE_VALUES.get(int(str(raw_mode)), "UNKNOWN")
    )
    unverified = ["stop_out_mode", "fifo"]
    hedging = None
    if margin_mode == "UNKNOWN":
        margin_mode = None
        unverified.insert(0, "margin_mode")
    elif margin_mode is not None:
        hedging = margin_mode == "RETAIL_HEDGING"
    return ProviderAccountPermissions(
        margin_mode=margin_mode,
        fifo=None,
        hedging_permitted=hedging,
        unverified=tuple(unverified),
    )


def _build_cost_evidence(
    evidence_id: str | None, checksum: str | None
) -> ProviderCostEvidenceReference | None:
    """Build the separate cost-evidence reference when supplied.

    Args:
        evidence_id: Dynamic cost-evidence identifier or None.
        checksum: Cost-evidence checksum or None.

    Returns:
        The typed reference, or None when no evidence is supplied.

    Raises:
        ValueError: If only one of identifier and checksum is supplied.
    """
    if evidence_id is None and checksum is None:
        return None
    if evidence_id is None or checksum is None:
        raise ValueError("cost evidence requires both an identifier and a checksum")
    return ProviderCostEvidenceReference(evidence_id=evidence_id, checksum=checksum)


__all__ = [
    "build_provider_specification_snapshot",
    "dump_provider_specification_snapshot",
    "parse_provider_specification_snapshot",
    "verify_provider_specification_snapshot",
]
