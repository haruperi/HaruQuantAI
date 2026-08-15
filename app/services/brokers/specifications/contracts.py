"""Immutable current provider specification snapshot contracts.

The snapshot states **current observation only**: it carries no effective
bounds and never invents historical validity. Missing required fields fail
closed at construction; dynamic commission/fee evidence stays a separate
typed reference rather than a guessed static symbol rate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import ClassVar

from app.utils import format_utc_timestamp

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

#: Calculation modes from the documented MQL5 ``SYMBOL_CALC_MODE`` members;
#: any unmapped provider value becomes ``UNKNOWN`` and fails canonical
#: eligibility rather than being guessed.
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

#: Rollover weekday names from verified MT5 ``swap_rollover3days`` values.
ROLLOVER_WEEKDAYS: tuple[str, ...] = (
    "SUNDAY",
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
)


def _require_text(value: str, name: str) -> None:
    """Reject blank required text.

    Args:
        value: Value supplied to the operation.
        name: Field name for the error message.

    Raises:
        ValueError: If the value is blank.
    """
    if not value.strip():
        message = f"{name} must not be empty"
        raise ValueError(message)


def _require_utc(value: datetime, name: str) -> None:
    """Reject naive or non-UTC timestamps.

    Args:
        value: Value supplied to the operation.
        name: Field name for the error message.

    Raises:
        ValueError: If the value is not aware UTC.
    """
    try:
        format_utc_timestamp(value)
    except Exception as error:
        message = f"{name} must be UTC-aware"
        raise ValueError(message) from error


def _optional_utc(value: datetime | None, name: str) -> None:
    """Validate an optional aware-UTC timestamp."""
    if value is not None:
        _require_utc(value, name)


def _require_finite(value: Decimal | None, name: str) -> None:
    """Reject non-finite decimal evidence.

    Args:
        value: Value supplied to the operation.
        name: Field name for the error message.

    Raises:
        ValueError: If the value is not finite.
    """
    if value is None or not value.is_finite():
        message = f"{name} is required and must be finite"
        raise ValueError(message)


def _optional_finite(value: Decimal | None, name: str) -> None:
    """Validate optional finite decimal evidence.

    Raises:
        ValueError: If the value is present and not finite.
    """
    if value is not None and not value.is_finite():
        message = f"{name} must be finite"
        raise ValueError(message)


def _require_checksum(value: str, name: str) -> None:
    """Require a lowercase 64-character SHA-256 digest.

    Args:
        value: Value supplied to the operation.
        name: Field name for the error message.

    Raises:
        ValueError: If the digest has the wrong shape.
    """
    _require_text(value, name)
    if len(value) != _SHA256_HEX_LENGTH or value != value.lower():
        message = f"{name} must be a lowercase sha256 digest"
        raise ValueError(message)


def _require_choice(value: str, allowed: tuple[str, ...], name: str) -> None:
    """Reject values outside the verified provider vocabulary.

    Args:
        value: Value supplied to the operation.
        allowed: Verified vocabulary members.
        name: Field name for the error message.

    Raises:
        ValueError: If the value is not admitted.
    """
    if value not in allowed:
        message = f"unknown {name}"
        raise ValueError(message)


class _Schema:
    """Stable schema metadata shared by the specification contracts."""

    CONTRACT_VERSION: ClassVar[str] = "v1"
    SCHEMA_ID: ClassVar[str]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderCostEvidenceReference(_Schema):
    """Typed reference to separate dynamic provider cost evidence.

    A commission/fee schedule is provider-account evidence, never a static
    symbol rate; this slot names and checksums that evidence without
    interpreting it.
    """

    SCHEMA_ID: ClassVar[str] = "brokers.provider_cost_evidence.v1"
    evidence_id: str
    checksum: str
    evidence_kind: str = "dynamic_commission_schedule"

    def __post_init__(self) -> None:
        """Validate the immutable reference invariants.

        Raises:
            ValueError: If any field is invalid.
        """
        _require_text(self.evidence_id, "evidence_id")
        _require_checksum(self.checksum, "cost evidence checksum")
        _require_text(self.evidence_kind, "evidence_kind")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderAccountPermissions(_Schema):
    """Account-level trading permissions bound to one snapshot observation.

    Fields the upstream provider contract does not expose stay ``None`` and
    are named in ``unverified``; the canonical parity path fails closed on
    them rather than inventing values.
    """

    SCHEMA_ID: ClassVar[str] = "brokers.provider_account_permissions.v1"
    margin_mode: str | None = None
    stop_out_mode: str | None = None
    fifo: bool | None = None
    hedging_permitted: bool | None = None
    unverified: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the permission block invariants.

        Raises:
            ValueError: If an unverified field is also populated.
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
    """Typed current provider specification observation for one symbol.

    Carries provider, server, redacted account digest, environment, terminal
    build, source revision, ``observed_at``, retrieval provenance, and a
    checksum over the canonical material. The type deliberately exposes no
    effective-from/effective-to fields: it is a current observation only.
    """

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
        """Validate the immutable snapshot invariants.

        Raises:
            ValueError: If any required field is missing or invalid.
        """
        self._validate_identity()
        self._validate_modes()
        self._validate_numerics()

    def _validate_identity(self) -> None:
        """Validate the identity, provenance, and text fields."""
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
        """Validate every mode vocabulary block.

        Raises:
            ValueError: If a mode list is empty or a value is unadmitted.
        """
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
        """Validate scalar, volume, and margin numeric bounds.

        Raises:
            ValueError: If a numeric bound is negative, non-finite, or
                inverted.
        """
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
]
