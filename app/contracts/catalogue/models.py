"""Strict Pydantic v2 wire records for the ratified Catalogue v1 contracts."""

from datetime import date
from decimal import Decimal
from fractions import Fraction
from itertools import pairwise
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from app.contracts.common.models import (
    ContentHash,
    CurrencyCode,
    DecimalValue,
    Money,
    OrderType,
    Rounding,
    TimeInForce,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)

# Closed asset-class enum from the ratified Catalogue v1 public records.
type AssetClass = Literal[
    "FOREX",
    "EQUITY",
    "ETF",
    "INDEX",
    "FUTURE",
    "OPTION",
    "BOND",
    "COMMODITY",
    "CRYPTO",
]

# Constrained local string aliases reused across catalogue records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
# Domain assumption: IANA zone names are limited to zone/path segments made of
# letters, digits, ``+``, ``-``, and ``_``; this is a syntactic wire check, not
# tzdb resolution.
type IanaTimezone = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9+\-_]+(?:/[A-Za-z0-9+\-_]+)*$"),
]
# Fixed-width wall-clock time; the pattern also bounds hour/minute/second
# ranges so fixed-format lexicographic order equals chronological order.
type LocalTime = Annotated[
    str,
    StringConstraints(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$"),
]

# Seconds in one local day and in one ISO week (Monday-based, day 1..7).
_SECONDS_PER_DAY = 86_400
_SECONDS_PER_WEEK = 604_800


def _local_seconds(value: str) -> int:
    """Return seconds after local midnight for a fixed HH:MM:SS string.

    Args:
        value: Local time string already validated by the ``LocalTime``
            alias; its fixed width makes positional slicing unambiguous.

    Returns:
        Seconds elapsed between local midnight and ``value``.
    """
    return int(value[0:2]) * 3600 + int(value[3:5]) * 60 + int(value[6:8])


def _half_open_intervals_overlap(
    start_a: str,
    end_a: str | None,
    start_b: str,
    end_b: str | None,
) -> bool:
    """Report whether two half-open UTC intervals share at least one instant.

    UtcTimestamp strings use one fixed-width format, so lexicographic order
    equals chronological order. A missing end extends to positive infinity.

    Args:
        start_a: Inclusive start of the first interval.
        end_a: Exclusive end of the first interval, or None when unbounded.
        start_b: Inclusive start of the second interval.
        end_b: Exclusive end of the second interval, or None when unbounded.

    Returns:
        True when the intervals intersect, False when they are disjoint.
    """
    return (end_a is None or start_b < end_a) and (end_b is None or start_a < end_b)


def _require_present(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that omits a required field.

    Args:
        fields: ``(field name, value)`` pairs that must not be None.

    Raises:
        ValueError: Any listed field is None.
    """
    for name, value in fields:
        if value is None:
            raise ValueError("required field is missing: " + name)


def _require_absent(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that sets a forbidden field.

    Args:
        fields: ``(field name, value)`` pairs that must be None.

    Raises:
        ValueError: Any listed field is not None.
    """
    for name, value in fields:
        if value is not None:
            raise ValueError("forbidden field is set: " + name)


class InstrumentRef(WireModel):
    """Reference to one canonical instrument identity."""

    instrument_id: Uuid7


class ProviderRef(WireModel):
    """Reference to one external data provider identity."""

    provider_id: Uuid7
    provider_name: NonEmptyStr


class BrokerRef(WireModel):
    """Reference to one broker identity."""

    broker_id: Uuid7
    broker_name: NonEmptyStr


class CostModelRef(WireModel):
    """Reference to one versioned trading cost model."""

    cost_model_id: Uuid7
    version: int = Field(ge=1)


class UniverseRef(WireModel):
    """Reference to one universe identity."""

    universe_id: Uuid7


class TradingInterval(WireModel):
    """One weekday-localized trading interval inside a session template.

    An interval whose close time is before its open time spans into the next
    local day; equal open and close times are invalid.
    """

    # ISO weekday: 1 (Monday) through 7 (Sunday).
    day_of_week: int = Field(ge=1, le=7)
    open_local: LocalTime
    close_local: LocalTime
    spans_next_day: bool = False

    @model_validator(mode="after")
    def validate_times(self) -> TradingInterval:
        """Reject equal open/close times and inconsistent day-span flags.

        Returns:
            The validated interval.

        Raises:
            ValueError: Open and close times are equal, or the
                ``spans_next_day`` flag contradicts the open/close ordering.
        """
        if self.open_local == self.close_local:
            raise ValueError("open_local and close_local must differ")
        if self.spans_next_day != (self.close_local < self.open_local):
            raise ValueError(
                "spans_next_day must be true exactly when close_local is "
                "before open_local"
            )
        return self


class CalendarEarlyClose(WireModel):
    """One calendar date on which trading closes earlier than usual."""

    date: date
    close_local: LocalTime


class MarketCalendarVersion(WireModel):
    """One immutable version of a market calendar.

    ``holiday_dates`` and ``early_closes`` must each be sorted and unique by
    date.
    """

    calendar_id: Uuid7
    version: int = Field(ge=1)
    timezone: IanaTimezone
    content_hash: ContentHash
    holiday_dates: tuple[date, ...] = ()
    early_closes: tuple[CalendarEarlyClose, ...] = ()

    @model_validator(mode="after")
    def validate_sorted_uniqueness(self) -> MarketCalendarVersion:
        """Reject unsorted or duplicate holidays and early closes.

        Returns:
            The validated calendar version.

        Raises:
            ValueError: ``holiday_dates`` or ``early_closes`` are not sorted
                and unique by date.
        """
        if self.holiday_dates != tuple(sorted(self.holiday_dates)) or len(
            set(self.holiday_dates)
        ) != len(self.holiday_dates):
            raise ValueError("holiday_dates must be sorted and unique")
        early_dates = tuple(early_close.date for early_close in self.early_closes)
        if early_dates != tuple(sorted(early_dates)) or len(set(early_dates)) != len(
            early_dates
        ):
            raise ValueError("early_closes must be sorted and unique by date")
        return self


class TradingSessionDefinition(WireModel):
    """One versioned, timezone-aware reusable trading session.

    Intervals may not overlap after normalizing overnight spans into the
    local week (a Sunday-night interval wraps into Monday).
    """

    session_id: Uuid7
    version: int = Field(ge=1)
    name: NonEmptyStr
    timezone: IanaTimezone
    intervals: tuple[TradingInterval, ...] = Field(min_length=1)
    calendar: MarketCalendarVersion
    end_of_day_policy: Literal["SESSION_CLOSE", "UTC_MIDNIGHT"]
    content_hash: ContentHash

    @model_validator(mode="after")
    def validate_interval_overlap(self) -> TradingSessionDefinition:
        """Reject trading intervals that overlap in the local week.

        Each interval is normalized to week-relative ``[start, end)`` second
        segments; an interval spanning past the end of the week wraps into
        the start of the week as an additional segment.

        Returns:
            The validated session definition.

        Raises:
            ValueError: Two intervals share at least one instant of the
                local week.
        """
        segments: list[tuple[int, int]] = []
        for interval in self.intervals:
            day_start = (interval.day_of_week - 1) * _SECONDS_PER_DAY
            start = day_start + _local_seconds(interval.open_local)
            end = day_start + _local_seconds(interval.close_local)
            if interval.spans_next_day:
                end += _SECONDS_PER_DAY
            if end > _SECONDS_PER_WEEK:
                segments.append((start, _SECONDS_PER_WEEK))
                segments.append((0, end - _SECONDS_PER_WEEK))
            else:
                segments.append((start, end))
        for index, (start_a, end_a) in enumerate(segments):
            for start_b, end_b in segments[index + 1 :]:
                if start_a < end_b and start_b < end_a:
                    raise ValueError("trading intervals may not overlap")
        return self


class OrderConstraints(WireModel):
    """Executable quantity bounds and supported order mechanics."""

    min_quantity: DecimalValue
    max_quantity: DecimalValue
    quantity_step: DecimalValue
    min_order_distance: DecimalValue
    supported_order_types: tuple[OrderType, ...] = Field(min_length=1)
    supported_time_in_force: tuple[TimeInForce, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_quantity_bounds(self) -> OrderConstraints:
        """Reject nonpositive increments and inconsistent quantity bounds.

        Returns:
            The validated order constraints.

        Raises:
            ValueError: Any decimal bound violates its ratified rule.
        """
        if Decimal(self.min_quantity) <= 0:
            raise ValueError("min_quantity must be positive")
        if Decimal(self.max_quantity) < Decimal(self.min_quantity):
            raise ValueError("max_quantity must be >= min_quantity")
        if Decimal(self.quantity_step) <= 0:
            raise ValueError("quantity_step must be positive")
        if Decimal(self.min_order_distance) < 0:
            raise ValueError("min_order_distance must be >= 0")
        return self


class InstrumentVersion(WireModel):
    """One immutable canonical instrument version.

    Effective validity is half-open; ``effective_to`` must be strictly after
    ``effective_from`` when present.
    """

    instrument_id: Uuid7
    version: int = Field(ge=1)
    symbol: NonEmptyStr
    display_name: NonEmptyStr
    asset_class: AssetClass
    base_currency: CurrencyCode
    quote_currency: CurrencyCode
    settlement_currency: CurrencyCode
    point_value: DecimalValue
    tick_size: DecimalValue
    price_decimals: int = Field(ge=0, le=18)
    quantity_multiplier: DecimalValue
    order_constraints: OrderConstraints
    default_spread: DecimalValue
    exchange: NonEmptyStr
    timezone: IanaTimezone
    session_id: Uuid7
    effective_from: UtcTimestamp
    content_hash: ContentHash
    effective_to: UtcTimestamp | None = None
    default_commission: Money | None = None
    default_swap_long: Money | None = None
    default_swap_short: Money | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_instrument_semantics(self) -> InstrumentVersion:
        """Reject inconsistent numeric, currency, and validity semantics.

        Returns:
            The validated instrument version.

        Raises:
            ValueError: A decimal bound, the tick-size precision, the
                base/quote currency identity, or the effective interval
                violates a ratified rule.
        """
        positive_fields = (
            ("point_value", self.point_value),
            ("tick_size", self.tick_size),
            ("quantity_multiplier", self.quantity_multiplier),
        )
        for name, value in positive_fields:
            if Decimal(value) <= 0:
                raise ValueError(name + " must be positive")
        if Decimal(self.default_spread) < 0:
            raise ValueError("default_spread must be >= 0")
        # The tick must be exactly representable at the declared precision.
        scaled_tick = Decimal(self.tick_size).scaleb(self.price_decimals)
        if scaled_tick != scaled_tick.to_integral_value():
            raise ValueError("tick_size must be representable at price_decimals")
        # Equal base and quote currencies identify a non-traded reference
        # index, which is the only asset class permitted to carry them.
        if self.base_currency == self.quote_currency and self.asset_class != "INDEX":
            raise ValueError(
                "base and quote currencies may be equal only for a reference INDEX"
            )
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class ProviderSymbolMapping(WireModel):
    """One versioned provider/broker symbol mapping for an instrument.

    The provider/broker/symbol plus effective interval is unique and mappings
    may not overlap; that cross-record invariant is enforced by the owning
    store because it spans multiple mapping records.
    """

    mapping_id: Uuid7
    instrument: InstrumentRef
    instrument_version: int = Field(ge=1)
    provider: ProviderRef
    provider_symbol: NonEmptyStr
    broker: BrokerRef | None
    effective_from: UtcTimestamp
    content_hash: ContentHash
    effective_to: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_effective_interval(self) -> ProviderSymbolMapping:
        """Reject a non-half-open effective interval.

        Returns:
            The validated mapping.

        Raises:
            ValueError: ``effective_to`` is not strictly after
                ``effective_from``.
        """
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class TradingRuleSet(WireModel):
    """One versioned set of rounding and cost rules for an instrument."""

    rule_set_id: Uuid7
    instrument: InstrumentRef
    instrument_version: int = Field(ge=1)
    order_constraints: OrderConstraints
    price_rounding: Rounding
    quantity_rounding: Literal["TOWARD_ZERO"]
    cost_model: CostModelRef
    effective_from: UtcTimestamp
    content_hash: ContentHash
    effective_to: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_effective_interval(self) -> TradingRuleSet:
        """Reject a non-half-open effective interval.

        Returns:
            The validated rule set.

        Raises:
            ValueError: ``effective_to`` is not strictly after
                ``effective_from``.
        """
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class UniverseMembership(WireModel):
    """One timebound membership row of an instrument in a universe."""

    instrument: InstrumentRef
    instrument_version: int = Field(ge=1)
    effective_from: UtcTimestamp
    effective_to: UtcTimestamp | None = None
    weight_hint: DecimalValue | None = None
    tags: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_membership(self) -> UniverseMembership:
        """Reject negative weights, unordered tags, and inverted intervals.

        Returns:
            The validated membership row.

        Raises:
            ValueError: ``weight_hint`` is negative, ``tags`` are not sorted
                and unique, or ``effective_to`` is not strictly after
                ``effective_from``.
        """
        if self.weight_hint is not None and Decimal(self.weight_hint) < 0:
            raise ValueError("weight_hint must be >= 0")
        if self.tags != tuple(sorted(self.tags)) or len(set(self.tags)) != len(
            self.tags
        ):
            raise ValueError("tags must be sorted and unique")
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class UniverseVersion(WireModel):
    """One immutable version of a named universe and its memberships.

    Member intervals must intersect the universe interval, and memberships
    of one instrument version may not carry overlapping intervals.
    """

    universe_id: Uuid7
    version: int = Field(ge=1)
    name: NonEmptyStr
    memberships: tuple[UniverseMembership, ...] = ()
    effective_from: UtcTimestamp
    content_hash: ContentHash
    effective_to: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_memberships(self) -> UniverseVersion:
        """Reject disjunct or duplicate-overlapping member intervals.

        Returns:
            The validated universe version.

        Raises:
            ValueError: A membership interval does not intersect the
                universe interval, two rows of the same instrument version
                overlap, or the universe interval is inverted.
        """
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        for index, membership in enumerate(self.memberships):
            if not _half_open_intervals_overlap(
                membership.effective_from,
                membership.effective_to,
                self.effective_from,
                self.effective_to,
            ):
                raise ValueError(
                    "membership interval must intersect the universe interval"
                )
            for prior in self.memberships[:index]:
                same_instrument = (
                    prior.instrument.instrument_id
                    == membership.instrument.instrument_id
                    and prior.instrument_version == membership.instrument_version
                )
                if same_instrument and _half_open_intervals_overlap(
                    prior.effective_from,
                    prior.effective_to,
                    membership.effective_from,
                    membership.effective_to,
                ):
                    raise ValueError(
                        "duplicate instrument/version intervals are invalid"
                    )
        return self


class FxRateObservation(WireModel):
    """One observed FX quote edge with a freshness deadline."""

    observation_id: Uuid7
    base_currency: CurrencyCode
    quote_currency: CurrencyCode
    rate: DecimalValue
    observed_at: UtcTimestamp
    source_provider: ProviderRef
    freshness_expires_at: UtcTimestamp
    content_hash: ContentHash
    source_instrument: InstrumentRef | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_observation(self) -> FxRateObservation:
        """Reject self-quotes, nonpositive rates, and stale-window misuse.

        Returns:
            The validated observation.

        Raises:
            ValueError: Base and quote currencies are equal, the rate is not
                positive, or freshness does not expire after observation.
        """
        if Decimal(self.rate) <= 0:
            raise ValueError("rate must be positive")
        if self.base_currency == self.quote_currency:
            raise ValueError("base and quote currencies must differ")
        if self.freshness_expires_at <= self.observed_at:
            raise ValueError("freshness_expires_at must be after observed_at")
        return self


class CurrencyConversionPath(WireModel):
    """One directed, continuous FX conversion path with its product rate."""

    from_currency: CurrencyCode
    to_currency: CurrencyCode
    as_of: UtcTimestamp
    observations: tuple[FxRateObservation, ...] = Field(min_length=1)
    converted_rate: DecimalValue
    hop_count: int = Field(ge=1)
    path_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_path(self) -> CurrencyConversionPath:
        """Reject broken chains, wrong hop counts, and inexact products.

        Returns:
            The validated conversion path.

        Raises:
            ValueError: The observations do not form a continuous directed
                path between the endpoint currencies, ``hop_count`` does not
                equal the observation count, the rate is not positive, or
                the canonical rate product is not numerically equal to
                ``converted_rate``.
        """
        if self.observations[0].base_currency != self.from_currency:
            raise ValueError("observations must start at from_currency")
        if self.observations[-1].quote_currency != self.to_currency:
            raise ValueError("observations must end at to_currency")
        for previous, current in pairwise(self.observations):
            if previous.quote_currency != current.base_currency:
                raise ValueError("observations must form a continuous path")
        if self.hop_count != len(self.observations):
            raise ValueError("hop_count must equal the observation count")
        if Decimal(self.converted_rate) <= 0:
            raise ValueError("converted_rate must be positive")
        # Fraction arithmetic is exact for finite decimals, so the canonical
        # multiplication check never suffers binary or context rounding.
        residual = Fraction(Decimal(self.converted_rate))
        for observation in self.observations:
            residual /= Fraction(Decimal(observation.rate))
        if residual != 1:
            raise ValueError("converted_rate must equal the canonical multiplication")
        return self


class CatalogueExchangePackage(WireModel):
    """One versioned interchange package of catalogue definitions.

    Every reference carried by the packaged records must either resolve to a
    record inside the package (instruments, sessions, calendars) or appear
    in ``external_refs``; providers, brokers, and cost models are never
    packaged, so their identifiers must always be declared external.
    """

    package_id: Uuid7
    exported_at: UtcTimestamp
    catalogue_schema_version: Literal[1]
    instrument_versions: tuple[InstrumentVersion, ...] = ()
    provider_mappings: tuple[ProviderSymbolMapping, ...] = ()
    sessions: tuple[TradingSessionDefinition, ...] = ()
    calendars: tuple[MarketCalendarVersion, ...] = ()
    trading_rules: tuple[TradingRuleSet, ...] = ()
    universes: tuple[UniverseVersion, ...] = ()
    content_hash: ContentHash
    external_refs: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_reference_resolution(self) -> CatalogueExchangePackage:
        """Reject unsorted external refs and unresolved references.

        Returns:
            The validated package.

        Raises:
            ValueError: ``external_refs`` is not sorted and unique, or any
                packaged reference resolves neither inside the package nor
                through ``external_refs``.
        """
        external = set(self.external_refs)
        unresolved: list[str] = []
        unresolved.extend(self._unresolved_session_references(external))
        unresolved.extend(self._unresolved_calendar_references(external))
        unresolved.extend(self._unresolved_mapping_references(external))
        unresolved.extend(self._unresolved_rule_references(external))
        unresolved.extend(self._unresolved_universe_references(external))
        if self.external_refs != tuple(sorted(self.external_refs)) or len(
            external
        ) != len(self.external_refs):
            raise ValueError("external_refs must be sorted and unique")
        if unresolved:
            raise ValueError(
                "every reference must resolve inside the package or appear "
                "in external_refs: " + ", ".join(unresolved)
            )
        return self

    def _unresolved_session_references(self, external: set[str]) -> list[str]:
        """Return messages for instrument session references that fail.

        Args:
            external: Identifiers declared through ``external_refs``.

        Returns:
            Messages for session references that resolve neither way.
        """
        session_ids = {session.session_id for session in self.sessions}
        return [
            "session " + record.session_id
            for record in self.instrument_versions
            if record.session_id not in session_ids
            and record.session_id not in external
        ]

    def _unresolved_calendar_references(self, external: set[str]) -> list[str]:
        """Return messages for session calendar references that fail.

        Args:
            external: Identifiers declared through ``external_refs``.

        Returns:
            Messages for calendar references that resolve neither way.
        """
        calendar_ids = {calendar.calendar_id for calendar in self.calendars}
        return [
            "calendar " + session.calendar.calendar_id
            for session in self.sessions
            if session.calendar.calendar_id not in calendar_ids
            and session.calendar.calendar_id not in external
        ]

    def _unresolved_mapping_references(self, external: set[str]) -> list[str]:
        """Return messages for provider mapping references that fail.

        Args:
            external: Identifiers declared through ``external_refs``.

        Returns:
            Messages for mapping references that resolve neither way.
        """
        instrument_ids = {record.instrument_id for record in self.instrument_versions}
        unresolved = [
            "instrument " + mapping.instrument.instrument_id
            for mapping in self.provider_mappings
            if mapping.instrument.instrument_id not in instrument_ids
            and mapping.instrument.instrument_id not in external
        ]
        unresolved.extend(
            "provider " + mapping.provider.provider_id
            for mapping in self.provider_mappings
            if mapping.provider.provider_id not in external
        )
        unresolved.extend(
            "broker " + mapping.broker.broker_id
            for mapping in self.provider_mappings
            if mapping.broker is not None and mapping.broker.broker_id not in external
        )
        return unresolved

    def _unresolved_rule_references(self, external: set[str]) -> list[str]:
        """Return messages for trading rule references that fail.

        Args:
            external: Identifiers declared through ``external_refs``.

        Returns:
            Messages for rule references that resolve neither way.
        """
        instrument_ids = {record.instrument_id for record in self.instrument_versions}
        unresolved = [
            "instrument " + rule.instrument.instrument_id
            for rule in self.trading_rules
            if rule.instrument.instrument_id not in instrument_ids
            and rule.instrument.instrument_id not in external
        ]
        # Cost models are never packaged, so they must always be external.
        unresolved.extend(
            "cost model " + rule.cost_model.cost_model_id
            for rule in self.trading_rules
            if rule.cost_model.cost_model_id not in external
        )
        return unresolved

    def _unresolved_universe_references(self, external: set[str]) -> list[str]:
        """Return messages for universe membership references that fail.

        Args:
            external: Identifiers declared through ``external_refs``.

        Returns:
            Messages for membership references that resolve neither way.
        """
        instrument_ids = {record.instrument_id for record in self.instrument_versions}
        return [
            "instrument " + membership.instrument.instrument_id
            for universe in self.universes
            for membership in universe.memberships
            if membership.instrument.instrument_id not in instrument_ids
            and membership.instrument.instrument_id not in external
        ]


class EffectiveInterval(WireModel):
    """Half-open effective UTC interval returned by session previews.

    This is the inline ``{from_at, to_at}`` record of
    ``DefineSessionsSuccess.effective_intervals``; it is not one of the 18
    registered public records.
    """

    from_at: UtcTimestamp
    to_at: UtcTimestamp

    @model_validator(mode="after")
    def validate_order(self) -> EffectiveInterval:
        """Reject inverted intervals.

        Returns:
            The validated interval.

        Raises:
            ValueError: ``to_at`` is not strictly after ``from_at``.
        """
        if self.to_at <= self.from_at:
            raise ValueError("to_at must be after from_at")
        return self


class CatalogInstrumentsRequest(WireModel):
    """Operation-discriminated instrument catalogue request.

    GET requires only ``instrument_ref``; LIST permits only paging; UPSERT
    requires only ``instrument_version`` plus an optional ``expected_version``;
    DELETE requires ``instrument_ref`` and ``expected_version``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["GET", "LIST", "UPSERT_VERSION", "DELETE_VERSION"]
    instrument_ref: InstrumentRef | None = None
    instrument_version: InstrumentVersion | None = None
    expected_version: int | None = Field(default=None, ge=1)
    page_size: int = Field(default=100, ge=1, le=500)
    page_cursor: str | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> CatalogInstrumentsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "GET":
                _require_present((("instrument_ref", self.instrument_ref),))
                _require_absent(
                    (
                        ("instrument_version", self.instrument_version),
                        ("expected_version", self.expected_version),
                        ("page_cursor", self.page_cursor),
                    )
                )
            case "LIST":
                _require_absent(
                    (
                        ("instrument_ref", self.instrument_ref),
                        ("instrument_version", self.instrument_version),
                        ("expected_version", self.expected_version),
                    )
                )
            case "UPSERT_VERSION":
                _require_present((("instrument_version", self.instrument_version),))
                _require_absent(
                    (
                        ("instrument_ref", self.instrument_ref),
                        ("page_cursor", self.page_cursor),
                    )
                )
            case "DELETE_VERSION":
                _require_present(
                    (
                        ("instrument_ref", self.instrument_ref),
                        ("expected_version", self.expected_version),
                    )
                )
                _require_absent(
                    (
                        ("instrument_version", self.instrument_version),
                        ("page_cursor", self.page_cursor),
                    )
                )
        return self


class CatalogInstrumentsSuccess(WireModel):
    """Successful instrument catalogue operation result."""

    request_id: Uuid7
    instruments: tuple[InstrumentVersion, ...] = ()
    next_cursor: str | None = None
    deleted: bool = False
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class MapProvidersRequest(WireModel):
    """Operation-discriminated provider and broker mapping request.

    UPSERT/DELETE require ``mapping`` and forbid resolution fields; RESOLVE
    requires ``provider``, ``provider_symbol``, and ``as_of`` and forbids
    ``mapping``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["RESOLVE", "UPSERT", "DELETE"]
    mapping: ProviderSymbolMapping | None = None
    provider: ProviderRef | None = None
    broker: BrokerRef | None = None
    provider_symbol: str | None = None
    as_of: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> MapProvidersRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "RESOLVE":
                _require_present(
                    (
                        ("provider", self.provider),
                        ("provider_symbol", self.provider_symbol),
                        ("as_of", self.as_of),
                    )
                )
                _require_absent((("mapping", self.mapping),))
            case "UPSERT" | "DELETE":
                _require_present((("mapping", self.mapping),))
                _require_absent(
                    (
                        ("provider", self.provider),
                        ("broker", self.broker),
                        ("provider_symbol", self.provider_symbol),
                        ("as_of", self.as_of),
                    )
                )
        return self


class MapProvidersSuccess(WireModel):
    """Successful provider and broker mapping operation result."""

    request_id: Uuid7
    mappings: tuple[ProviderSymbolMapping, ...] = ()
    deleted: bool = False
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class DefineSessionsRequest(WireModel):
    """Operation-discriminated session and calendar request.

    GET requires only ``session_id``; each UPSERT requires only its record;
    PREVIEW requires ``session_id`` with ``to_at`` after ``from_at``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["GET", "UPSERT_SESSION", "UPSERT_CALENDAR", "PREVIEW"]
    session: TradingSessionDefinition | None = None
    calendar: MarketCalendarVersion | None = None
    session_id: Uuid7 | None = None
    from_at: UtcTimestamp | None = None
    to_at: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DefineSessionsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing, forbidden fields are
                set, or the PREVIEW window is inverted.
        """
        match self.operation:
            case "GET":
                _require_present((("session_id", self.session_id),))
                _require_absent(
                    (
                        ("session", self.session),
                        ("calendar", self.calendar),
                        ("from_at", self.from_at),
                        ("to_at", self.to_at),
                    )
                )
            case "UPSERT_SESSION":
                _require_present((("session", self.session),))
                _require_absent(
                    (
                        ("calendar", self.calendar),
                        ("session_id", self.session_id),
                        ("from_at", self.from_at),
                        ("to_at", self.to_at),
                    )
                )
            case "UPSERT_CALENDAR":
                _require_present((("calendar", self.calendar),))
                _require_absent(
                    (
                        ("session", self.session),
                        ("session_id", self.session_id),
                        ("from_at", self.from_at),
                        ("to_at", self.to_at),
                    )
                )
            case "PREVIEW":
                _require_present(
                    (
                        ("session_id", self.session_id),
                        ("from_at", self.from_at),
                        ("to_at", self.to_at),
                    )
                )
                _require_absent(
                    (
                        ("session", self.session),
                        ("calendar", self.calendar),
                    )
                )
                if (
                    self.to_at is not None
                    and self.from_at is not None
                    and self.to_at <= self.from_at
                ):
                    raise ValueError("PREVIEW requires to_at after from_at")
        return self


class DefineSessionsSuccess(WireModel):
    """Successful session and calendar operation result."""

    request_id: Uuid7
    session: TradingSessionDefinition | None = None
    calendar: MarketCalendarVersion | None = None
    effective_intervals: tuple[EffectiveInterval, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class DefineTradingRulesRequest(WireModel):
    """Operation-discriminated trading rules and costs request.

    UPSERT requires only ``rule_set``; GET requires identity and time;
    NORMALIZE requires identity and time plus at least ``price`` or
    ``quantity``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["GET", "UPSERT", "NORMALIZE"]
    rule_set: TradingRuleSet | None = None
    instrument: InstrumentRef | None = None
    instrument_version: int | None = Field(default=None, ge=1)
    as_of: UtcTimestamp | None = None
    price: DecimalValue | None = None
    quantity: DecimalValue | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DefineTradingRulesRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing, forbidden fields are
                set, or NORMALIZE carries neither price nor quantity.
        """
        match self.operation:
            case "UPSERT":
                _require_present((("rule_set", self.rule_set),))
                _require_absent(
                    (
                        ("instrument", self.instrument),
                        ("instrument_version", self.instrument_version),
                        ("as_of", self.as_of),
                        ("price", self.price),
                        ("quantity", self.quantity),
                    )
                )
            case "GET":
                _require_present(
                    (
                        ("instrument", self.instrument),
                        ("instrument_version", self.instrument_version),
                        ("as_of", self.as_of),
                    )
                )
                _require_absent(
                    (
                        ("rule_set", self.rule_set),
                        ("price", self.price),
                        ("quantity", self.quantity),
                    )
                )
            case "NORMALIZE":
                _require_present(
                    (
                        ("instrument", self.instrument),
                        ("instrument_version", self.instrument_version),
                        ("as_of", self.as_of),
                    )
                )
                _require_absent((("rule_set", self.rule_set),))
                if self.price is None and self.quantity is None:
                    raise ValueError("NORMALIZE requires price or quantity")
        return self


class DefineTradingRulesSuccess(WireModel):
    """Successful trading rules and costs operation result."""

    request_id: Uuid7
    rule_set: TradingRuleSet | None = None
    normalized_price: DecimalValue | None = None
    normalized_quantity: DecimalValue | None = None
    cost_model: CostModelRef | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ManageUniversesRequest(WireModel):
    """Operation-discriminated universe management request.

    UPSERT requires only ``universe_version``; GET requires only
    ``universe_ref``; RESOLVE_MEMBERS requires ``universe_ref`` and time.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["GET", "UPSERT_VERSION", "RESOLVE_MEMBERS"]
    universe_ref: UniverseRef | None = None
    universe_version: UniverseVersion | None = None
    as_of: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ManageUniversesRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "GET":
                _require_present((("universe_ref", self.universe_ref),))
                _require_absent(
                    (
                        ("universe_version", self.universe_version),
                        ("as_of", self.as_of),
                    )
                )
            case "UPSERT_VERSION":
                _require_present((("universe_version", self.universe_version),))
                _require_absent(
                    (
                        ("universe_ref", self.universe_ref),
                        ("as_of", self.as_of),
                    )
                )
            case "RESOLVE_MEMBERS":
                _require_present(
                    (
                        ("universe_ref", self.universe_ref),
                        ("as_of", self.as_of),
                    )
                )
                _require_absent((("universe_version", self.universe_version),))
        return self


class ManageUniversesSuccess(WireModel):
    """Successful universe management operation result."""

    request_id: Uuid7
    universe: UniverseVersion | None = None
    members: tuple[UniverseMembership, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ConvertCurrenciesRequest(WireModel):
    """Pure currency conversion query request."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    amount: Money
    to_currency: CurrencyCode
    as_of: UtcTimestamp
    freshness_limit_seconds: int = Field(ge=1)
    max_hops: int = Field(default=3, ge=1, le=4)
    schema_version: Literal[1] = 1


class ConvertCurrenciesSuccess(WireModel):
    """Successful currency conversion query result."""

    request_id: Uuid7
    converted: Money
    path: CurrencyConversionPath
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ExchangeCatalogueRequest(WireModel):
    """Operation-discriminated catalogue interchange request.

    EXPORT forbids ``package``; VALIDATE_IMPORT and IMPORT require it.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["EXPORT", "VALIDATE_IMPORT", "IMPORT"]
    package: CatalogueExchangePackage | None = None
    selected_instrument_ids: tuple[Uuid7, ...] = ()
    conflict_policy: Literal["REJECT", "KEEP_EXISTING", "CREATE_NEW_VERSION"] = "REJECT"
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ExchangeCatalogueRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: EXPORT carries a package or an import operation
                omits the package.
        """
        match self.operation:
            case "EXPORT":
                _require_absent((("package", self.package),))
            case "VALIDATE_IMPORT" | "IMPORT":
                _require_present((("package", self.package),))
        return self


class ExchangeCatalogueSuccess(WireModel):
    """Successful catalogue interchange operation result."""

    request_id: Uuid7
    package: CatalogueExchangePackage | None = None
    imported_refs: tuple[Uuid7, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# AssetClass is a PEP 695 ``type`` alias, not a class, so it cannot be
# registered in WIRE_MODELS; EffectiveInterval is an inline success-record
# component rather than one of the registered public records.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "InstrumentRef": InstrumentRef,
    "InstrumentVersion": InstrumentVersion,
    "ProviderRef": ProviderRef,
    "BrokerRef": BrokerRef,
    "ProviderSymbolMapping": ProviderSymbolMapping,
    "TradingSessionDefinition": TradingSessionDefinition,
    "MarketCalendarVersion": MarketCalendarVersion,
    "TradingInterval": TradingInterval,
    "TradingRuleSet": TradingRuleSet,
    "OrderConstraints": OrderConstraints,
    "CostModelRef": CostModelRef,
    "UniverseRef": UniverseRef,
    "UniverseVersion": UniverseVersion,
    "UniverseMembership": UniverseMembership,
    "FxRateObservation": FxRateObservation,
    "CurrencyConversionPath": CurrencyConversionPath,
    "CatalogueExchangePackage": CatalogueExchangePackage,
    "CatalogInstrumentsRequest": CatalogInstrumentsRequest,
    "CatalogInstrumentsSuccess": CatalogInstrumentsSuccess,
    "MapProvidersRequest": MapProvidersRequest,
    "MapProvidersSuccess": MapProvidersSuccess,
    "DefineSessionsRequest": DefineSessionsRequest,
    "DefineSessionsSuccess": DefineSessionsSuccess,
    "DefineTradingRulesRequest": DefineTradingRulesRequest,
    "DefineTradingRulesSuccess": DefineTradingRulesSuccess,
    "ManageUniversesRequest": ManageUniversesRequest,
    "ManageUniversesSuccess": ManageUniversesSuccess,
    "ConvertCurrenciesRequest": ConvertCurrenciesRequest,
    "ConvertCurrenciesSuccess": ConvertCurrenciesSuccess,
    "ExchangeCatalogueRequest": ExchangeCatalogueRequest,
    "ExchangeCatalogueSuccess": ExchangeCatalogueSuccess,
}
