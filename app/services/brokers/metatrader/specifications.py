# mypy: ignore-errors
"""MetaTrader 5 provider specification snapshot observations (provider truth).

The snapshot represents current provider observation only: it carries no
effective bounds and never invents historical validity. Missing required
fields fail closed at construction. Dynamic cost evidence remains a separate
typed reference.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from dataclasses import fields as dataclass_fields
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from app.services.brokers.metatrader._legacy_types import StandardResponse

from app.kernel.serialization import canonical_json
from app.kernel.time import format_utc_timestamp

logger = logging.getLogger(__name__)

#: Length of a lowercase hexadecimal SHA-256 digest.
_SHA256_HEX_LENGTH = 64

#: Filling policies admitted by verified MT5 ``filling_mode`` bit flags.
FILLING_MODES: tuple[str, ...] = ("FOK", "IOC", "RETURN")

#: Order types admitted by verified MT5 ``order_mode`` bit flags.
ORDER_TYPE_FLAGS: tuple[tuple[int, str], ...] = (
    (1, "MARKET"),
    (2, "LIMIT"),
    (4, "STOP"),
    (8, "STOP_LIMIT"),
    (16, "CLOSE_BY"),
    (32, "STOPLOSS"),
    (64, "TAKEPROFIT"),
)

#: Expiration policies admitted by verified MT5 ``expiration_mode`` bit flags.
EXPIRATION_MODE_FLAGS: tuple[tuple[int, str], ...] = (
    (1, "GTC"),
    (2, "DAY"),
    (4, "SPECIFIED"),
    (8, "SPECIFIED_DAY"),
)

#: Order-lifetime modes from verified MT5 ``order_gtc_mode`` values.
GTC_MODES: tuple[str, ...] = ("GTC", "DAILY", "SPECIFIED")

#: Symbol execution modes from verified MT5 ``trade_exemode`` values.
EXECUTION_MODES: tuple[str, ...] = (
    "REQUEST",
    "INSTANT",
    "MARKET",
    "EXCHANGE",
)

#: Symbol trade modes from the verified in-repo MT5 ``trade_mode`` mapping.
TRADE_MODES: tuple[str, ...] = (
    "DISABLED",
    "LONGONLY",
    "SHORTONLY",
    "CLOSEONLY",
    "FULL",
)

#: Swap modes from the verified in-repo MT5 ``swap_mode`` mapping.
SWAP_MODES: tuple[str, ...] = (
    "DISABLED",
    "POINTS",
    "CURRENCY_SYMBOL",
    "CURRENCY_MARGIN",
    "CURRENCY_DEPOSIT",
    "INTEREST_CURRENT",
    "REOPEN_CURRENT",
    "REOPEN_BID",
)

#: Calculation modes from the documented MQL5 ``SYMBOL_CALC_MODE`` members.
CALCULATION_MODES: tuple[str, ...] = (
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
    "UNKNOWN",
)

#: Rollover weekday names plus MT5's observed non-weekday sentinel.
ROLLOVER_WEEKDAYS: tuple[str, ...] = (
    "SUNDAY",
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "UNSPECIFIED",
)

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


def _require_text(value: str, name: str) -> None:
    if not value.strip():
        message = f"{name} must not be empty"
        raise ValueError(message)


def _require_utc(value: datetime, name: str) -> None:
    try:
        format_utc_timestamp(value)
    except Exception as error:
        message = f"{name} must be UTC-aware"
        raise ValueError(message) from error


def _require_finite(value: Decimal | None, name: str) -> None:
    if value is None or not value.is_finite():
        message = f"{name} is required and must be finite"
        raise ValueError(message)


def _optional_finite(value: Decimal | None, name: str) -> None:
    if value is not None and not value.is_finite():
        message = f"{name} must be finite"
        raise ValueError(message)


def _require_checksum(value: str, name: str) -> None:
    _require_text(value, name)
    if len(value) != _SHA256_HEX_LENGTH or value != value.lower():
        message = f"{name} must be a lowercase sha256 digest"
        raise ValueError(message)


def _require_choice(value: str, allowed: tuple[str, ...], name: str) -> None:
    if value not in allowed:
        message = f"unknown {name}"
        raise ValueError(message)


class _Schema:
    CONTRACT_VERSION: ClassVar[str] = "v1"
    SCHEMA_ID: ClassVar[str]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderCostEvidenceReference(_Schema):
    """Typed reference to separate dynamic provider cost evidence."""

    SCHEMA_ID: ClassVar[str] = "brokers.provider_cost_evidence.v1"
    evidence_id: str
    checksum: str
    evidence_kind: str = "dynamic_commission_schedule"

    def __post_init__(self) -> None:
        """Validate cost evidence fields fail closed."""
        _require_text(self.evidence_id, "evidence_id")
        _require_checksum(self.checksum, "cost evidence checksum")
        _require_text(self.evidence_kind, "evidence_kind")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderAccountPermissions(_Schema):
    """Account-level trading permissions bound to one snapshot observation."""

    SCHEMA_ID: ClassVar[str] = "brokers.provider_account_permissions.v1"
    margin_mode: str | None = None
    stop_out_mode: str | None = None
    fifo: bool | None = None
    hedging_permitted: bool | None = None
    unverified: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate account permission fields and unverified overlap.

        Raises:
            ValueError: If unverified fields overlap with populated fields.
        """
        populated = {
            "margin_mode": self.margin_mode,
            "stop_out_mode": self.stop_out_mode,
            "fifo": self.fifo,
            "hedging_permitted": self.hedging_permitted,
        }
        overlap = sorted(
            name for name in self.unverified if populated[name] is not None
        )
        if overlap:
            message = "unverified fields must remain unpopulated: " + ",".join(overlap)
            raise ValueError(message)
        if self.margin_mode is not None:
            _require_choice(
                self.margin_mode, ("NETTING", "RETAIL_HEDGING"), "margin_mode"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderSpecificationSnapshot(_Schema):
    """Typed current provider specification observation for one symbol."""

    SCHEMA_ID: ClassVar[str] = "brokers.provider_specification.v1"
    broker: str
    server: str
    account_digest: str
    environment: str
    terminal_build: str
    source_revision: str
    observed_at: datetime
    retrieval_provenance: str
    provider_symbol: str
    filling_modes: tuple[str, ...]
    order_types: tuple[str, ...]
    expiration_modes: tuple[str, ...]
    gtc_mode: str
    execution_mode: str
    trade_mode: str
    calculation_mode: str
    stops_level_points: int
    freeze_level_points: int
    volume_min: Decimal
    volume_max: Decimal
    volume_step: Decimal
    directional_volume_limit: Decimal | None
    point: Decimal
    digits: int
    tick_size: Decimal
    tick_value: Decimal | None
    tick_value_profit: Decimal | None
    tick_value_loss: Decimal | None
    contract_size: Decimal
    base_currency: str
    profit_currency: str
    margin_currency: str
    margin_initial: Decimal | None
    margin_maintenance: Decimal | None
    margin_hedged: Decimal | None
    margin_hedged_use_leg: bool | None
    swap_mode: str
    swap_long: Decimal
    swap_short: Decimal
    swap_rollover3days: str
    account_permissions: ProviderAccountPermissions = field(
        default_factory=ProviderAccountPermissions
    )
    cost_evidence: ProviderCostEvidenceReference | None = None
    checksum: str = ""

    def __post_init__(self) -> None:
        """Validate snapshot identity, modes, and numerics fail closed."""
        self._validate_identity()
        self._validate_modes()
        self._validate_numerics()

    def _validate_identity(self) -> None:
        for name in (
            "broker",
            "server",
            "account_digest",
            "environment",
            "terminal_build",
            "source_revision",
            "retrieval_provenance",
            "provider_symbol",
            "base_currency",
            "profit_currency",
            "margin_currency",
        ):
            _require_text(getattr(self, name), name)
        _require_utc(self.observed_at, "observed_at")
        if self.checksum:
            _require_checksum(self.checksum, "checksum")

    def _validate_modes(self) -> None:
        mode_blocks: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
            (self.filling_modes, FILLING_MODES, "filling mode"),
            (
                self.order_types,
                tuple(name for _, name in ORDER_TYPE_FLAGS),
                "order type",
            ),
            (
                self.expiration_modes,
                tuple(name for _, name in EXPIRATION_MODE_FLAGS),
                "expiration mode",
            ),
        )
        for values, allowed, label in mode_blocks:
            if not values:
                message = label + "s must not be empty"
                raise ValueError(message)
            for value in values:
                _require_choice(value, allowed, label)
        for value, allowed, name in (
            (self.gtc_mode, GTC_MODES, "gtc_mode"),
            (self.execution_mode, EXECUTION_MODES, "execution_mode"),
            (self.trade_mode, TRADE_MODES, "trade_mode"),
            (self.calculation_mode, CALCULATION_MODES, "calculation_mode"),
            (self.swap_mode, SWAP_MODES, "swap_mode"),
            (self.swap_rollover3days, ROLLOVER_WEEKDAYS, "swap_rollover3days"),
        ):
            _require_choice(value, allowed, name)

    def _validate_numerics(self) -> None:
        if self.digits < 0:
            raise ValueError("digits must not be negative")
        if self.stops_level_points < 0 or self.freeze_level_points < 0:
            raise ValueError("stop and freeze levels must not be negative")
        for name in (
            "volume_min",
            "volume_max",
            "volume_step",
            "point",
            "tick_size",
            "contract_size",
            "swap_long",
            "swap_short",
        ):
            _require_finite(getattr(self, name), name)
        for name in (
            "directional_volume_limit",
            "tick_value",
            "tick_value_profit",
            "tick_value_loss",
            "margin_initial",
            "margin_maintenance",
            "margin_hedged",
        ):
            _optional_finite(getattr(self, name), name)
        if self.volume_min <= 0 or self.volume_step <= 0:
            raise ValueError("volume minimum and step must be positive")
        if self.volume_max < self.volume_min:
            raise ValueError("volume maximum is below the minimum")
        if self.point <= 0 or self.tick_size <= 0 or self.contract_size <= 0:
            raise ValueError("point, tick size, and contract size must be positive")


def _field(value: object, name: str) -> object:
    result = _optional(value, name)
    if result is None:
        message = "missing required provider specification field: " + name
        raise ValueError(message)
    return result


def _optional(value: object, name: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(name)
    if hasattr(value, "_asdict"):
        as_dict = value._asdict
        return dict(as_dict()).get(name)
    return getattr(value, name, None)


def _decimal(value: object, name: str) -> Decimal:
    if value is None or isinstance(value, bool):
        message = "missing required provider specification field: " + name
        raise ValueError(message)
    parsed = Decimal(str(value))
    if not parsed.is_finite():
        message = "provider specification field is not finite: " + name
        raise ValueError(message)
    return parsed


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    return Decimal(str(value))


def _int(value: object, name: str) -> int:
    if value is None or isinstance(value, bool):
        message = "missing required provider specification field: " + name
        raise ValueError(message)
    return int(str(value))


def _text(value: object, name: str) -> str:
    if value is None or not str(value).strip():
        message = "missing required provider specification field: " + name
        raise ValueError(message)
    return str(value).strip()


def _index_name(value: int, table: tuple[str, ...], name: str, unknown: str) -> str:
    if value < 0:
        message = name + " must not be negative"
        raise ValueError(message)
    if value < len(table):
        return table[value]
    return unknown


def _flag_names(mask: int, flags: tuple[tuple[int, str], ...]) -> tuple[str, ...]:
    return tuple(sorted(name for bit, name in flags if mask & bit))


def _account_digest(broker: str, server: str, account_id: str) -> str:
    material = "brokers.account.v1|" + broker + "|" + server + "|" + account_id
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _checksum(snapshot_fields: Mapping[str, object]) -> str:
    return hashlib.sha256(
        canonical_json(dict(snapshot_fields)).encode("utf-8")
    ).hexdigest()


def _json_safe(value: object) -> object:
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
    snapshot: object,
) -> dict[str, object]:
    """Return the canonical JSON-safe mapping of one snapshot."""
    return {
        entry.name: _json_safe(getattr(snapshot, entry.name))
        for entry in dataclass_fields(ProviderSpecificationSnapshot)
    }


def parse_provider_specification_snapshot(
    value: Mapping[str, object],
) -> ProviderSpecificationSnapshot:
    """Parse one canonical snapshot mapping back into the typed contract.

    Args:
        value: Canonical snapshot dictionary representation.

    Returns:
        Validated typed ProviderSpecificationSnapshot instance.

    Raises:
        ValueError: If effective bounds, schema keys, or checksum fail validation.
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
    return None if value is None else str(value)


def _convert_permissions(raw: object) -> ProviderAccountPermissions:
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
        symbol_info: Raw provider symbol information mapping or object.
        broker: Broker identifier string.
        server: Provider server name.
        account_id: Account identifier for digest construction.
        environment: Environment string.
        terminal_build: Terminal build identifier.
        source_revision: Provider source revision identifier.
        observed_at: Aware UTC observation timestamp.
        retrieval_provenance: Provenance tag string.
        account_info: Optional raw account info mapping or object.
        cost_evidence_id: Optional dynamic cost evidence identifier.
        cost_evidence_checksum: Optional dynamic cost evidence checksum.

    Returns:
        Complete checksummed ProviderSpecificationSnapshot.

    Raises:
        ValueError: If mandatory fields or numeric bounds fail validation.
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
        message = "swap_rollover3days is outside the verified provider range"
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
    snapshot: object,
) -> bool:
    """Recompute and compare the snapshot checksum.

    Args:
        snapshot: Candidate snapshot instance.

    Returns:
        True if the recomputed checksum matches snapshot.checksum.

    Raises:
        ValueError: If snapshot has no checksum.
    """
    checksum_val = getattr(snapshot, "checksum", None)
    if not checksum_val:
        raise ValueError("snapshot checksum is required for verification")
    material = dump_provider_specification_snapshot(snapshot)
    material.pop("checksum", None)
    return bool(_checksum(material) == checksum_val)


def get_provider_specification_snapshot_field(
    snapshot: object,
    field: str,
) -> object:
    """Read one named snapshot field.

    Args:
        snapshot: Snapshot instance.
        field: Name of the field to retrieve.

    Returns:
        Field value from the serialized snapshot mapping.

    Raises:
        ValueError: If the field name is not recognized.
    """
    dumped = dump_provider_specification_snapshot(snapshot)
    if field not in dumped:
        message = "unknown snapshot field: " + field
        raise ValueError(message)
    return dumped[field]


async def get_broker_provider_specification(
    adapter: object, symbol: str
) -> StandardResponse[ProviderSpecificationSnapshot]:
    """Read one current provider specification snapshot through the adapter.

    Args:
        adapter: Target broker adapter.
        symbol: Exact provider-native symbol name.

    Returns:
        StandardResponse containing the ProviderSpecificationSnapshot.
    """
    return await adapter.get_provider_specification(symbol)


def _build_permissions(account_info: object | None) -> ProviderAccountPermissions:
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
    if evidence_id is None and checksum is None:
        return None
    if evidence_id is None or checksum is None:
        raise ValueError("cost evidence requires both an identifier and a checksum")
    return ProviderCostEvidenceReference(evidence_id=evidence_id, checksum=checksum)


__all__ = [
    "CALCULATION_MODES",
    "EXECUTION_MODES",
    "EXPIRATION_MODE_FLAGS",
    "FILLING_MODES",
    "GTC_MODES",
    "ORDER_TYPE_FLAGS",
    "ROLLOVER_WEEKDAYS",
    "SWAP_MODES",
    "TRADE_MODES",
    "ProviderAccountPermissions",
    "ProviderCostEvidenceReference",
    "ProviderSpecificationSnapshot",
    "build_provider_specification_snapshot",
    "dump_provider_specification_snapshot",
    "get_broker_provider_specification",
    "get_provider_specification_snapshot_field",
    "parse_provider_specification_snapshot",
    "verify_provider_specification_snapshot",
]
