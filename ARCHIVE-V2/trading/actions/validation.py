"""Local trading action validation and parameter normalization primitives.

This module implements broker-independent order parameter validation:
``decimal.Decimal`` normalization to dynamic instrument precision,
direction-aware stop-loss/take-profit geometry, margin sufficiency, market
session evidence, time-in-force capability, execution protections (mandatory
slippage and price collars), the immutable fat-finger notional ceiling,
defense-in-depth rails, and short-locate verification.

Every check accepts explicit evidence inputs (symbol constraints, account
margin context, conversion-rate evidence, session evidence, locate snapshots)
rather than reading broker state directly, so the exact same validation runs
identically under ``route="sim"`` and ``route="live"`` (TRD-XM-001). Callers
resolve the evidence (e.g. via ``trading/info/`` facades) and pass it in.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_UP, Decimal
from enum import StrEnum

from app.services.trading.contracts import (
    JsonObject,
    TimeInForce,
    TradingContract,
    TradingRoute,
)
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)
from app.utils.logger import logger
from pydantic import Field, model_validator

BPS_DENOMINATOR = Decimal(10_000)
LIVE_SENSITIVE_ROUTES = frozenset({TradingRoute.LIVE})
DEFAULT_SUPPORTED_TIF: tuple[TimeInForce, ...] = (
    TimeInForce.GTC,
    TimeInForce.IOC,
    TimeInForce.FOK,
    TimeInForce.GTD,
    TimeInForce.DAY,
)


class OrderSide(StrEnum):
    """Trade direction for an order intent."""

    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    """Local order type classification used to route validation rules."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


PENDING_ORDER_TYPES = frozenset({OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT})


class SymbolTradingConstraints(TradingContract):
    """Dynamically resolved broker symbol trading constraints.

    Attributes:
        symbol: Instrument symbol.
        digits: Price precision digits.
        volume_min: Minimum tradable volume.
        volume_max: Maximum tradable volume.
        volume_step: Volume increment step.
        tick_size: Minimum price increment.
        min_stop_distance: Minimum absolute SL/TP distance from the market.
        contract_size: Contract size per one lot of volume.
        quote_currency: Instrument quote currency.
        price_collar_bps: Allowed pending-order price deviation in basis
            points from the current market reference price.
    """

    symbol: str
    digits: int = Field(ge=0)
    volume_min: Decimal = Field(gt=0)
    volume_max: Decimal = Field(gt=0)
    volume_step: Decimal = Field(gt=0)
    tick_size: Decimal = Field(gt=0)
    min_stop_distance: Decimal = Field(default=Decimal(0), ge=0)
    contract_size: Decimal = Field(gt=0)
    quote_currency: str
    price_collar_bps: Decimal = Field(default=Decimal(50), ge=0)

    @model_validator(mode="after")
    def validate_constraints(self) -> SymbolTradingConstraints:
        """Validate symbol constraint consistency.

        Returns:
            SymbolTradingConstraints: Validated constraints.

        Raises:
            ValueError: If identifiers are blank or volume bounds invert.
        """
        logger.info("Validating symbol trading constraints for {}.", self.symbol)
        if not self.symbol.strip():
            raise ValueError("symbol must be non-empty.")
        if not self.quote_currency.strip():
            raise ValueError("quote_currency must be non-empty.")
        if self.volume_min > self.volume_max:
            raise ValueError("volume_min must not exceed volume_max.")
        return self


class AccountMarginContext(TradingContract):
    """Account margin evidence used for pre-trade margin sufficiency checks.

    Attributes:
        account_currency: Account base currency.
        leverage: Account leverage ratio.
        free_margin: Currently available free margin in account currency.
    """

    account_currency: str
    leverage: int = Field(gt=0)
    free_margin: Decimal = Field(ge=0)

    @model_validator(mode="after")
    def validate_margin_context(self) -> AccountMarginContext:
        """Validate account margin context fields.

        Returns:
            AccountMarginContext: Validated margin context.

        Raises:
            ValueError: If the account currency is blank.
        """
        logger.info("Validating account margin context for {}.", self.account_currency)
        if not self.account_currency.strip():
            raise ValueError("account_currency must be non-empty.")
        return self


class ConversionRateEvidence(TradingContract):
    """Currency conversion-rate evidence with a configured freshness TTL.

    Attributes:
        from_currency: Source currency code.
        to_currency: Target currency code.
        rate: Conversion rate from source to target currency.
        source: Evidence source identifier.
        captured_at: Evidence capture timestamp.
        freshness_age_ms: Evidence age in milliseconds at validation time.
        ttl_ms: Configured freshness time-to-live in milliseconds.
    """

    from_currency: str
    to_currency: str
    rate: Decimal = Field(gt=0)
    source: str
    captured_at: str
    freshness_age_ms: int = Field(ge=0)
    ttl_ms: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_conversion_evidence(self) -> ConversionRateEvidence:
        """Validate conversion-rate evidence identifiers.

        Returns:
            ConversionRateEvidence: Validated conversion-rate evidence.

        Raises:
            ValueError: If currency codes or source are blank.
        """
        logger.info(
            "Validating conversion-rate evidence {}->{}.",
            self.from_currency,
            self.to_currency,
        )
        if not self.from_currency.strip() or not self.to_currency.strip():
            raise ValueError("from_currency and to_currency must be non-empty.")
        if not self.source.strip():
            raise ValueError("source must be non-empty.")
        return self

    def is_fresh(self) -> bool:
        """Return whether the conversion-rate evidence is within its TTL.

        Returns:
            bool: True when the evidence has not exceeded its TTL.
        """
        logger.debug(
            "Checking conversion-rate freshness age={} ttl={}.",
            self.freshness_age_ms,
            self.ttl_ms,
        )
        return self.freshness_age_ms <= self.ttl_ms


class MarketSessionEvidence(TradingContract):
    """Trading-calendar session evidence published by the data module.

    Attributes:
        symbol: Instrument symbol.
        source: Evidence source identifier.
        is_open: Whether the instrument session is currently open.
        freshness_age_ms: Evidence age in milliseconds at validation time.
        ttl_ms: Configured freshness time-to-live in milliseconds.
    """

    symbol: str
    source: str
    is_open: bool
    freshness_age_ms: int = Field(ge=0)
    ttl_ms: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_session_evidence(self) -> MarketSessionEvidence:
        """Validate market session evidence identifiers.

        Returns:
            MarketSessionEvidence: Validated session evidence.

        Raises:
            ValueError: If symbol or source are blank.
        """
        logger.info("Validating market session evidence for {}.", self.symbol)
        if not self.symbol.strip() or not self.source.strip():
            raise ValueError("symbol and source must be non-empty.")
        return self

    def is_fresh(self) -> bool:
        """Return whether the session evidence is within its TTL.

        Returns:
            bool: True when the evidence has not exceeded its TTL.
        """
        logger.debug(
            "Checking market session freshness age={} ttl={}.",
            self.freshness_age_ms,
            self.ttl_ms,
        )
        return self.freshness_age_ms <= self.ttl_ms


class LocateSnapshot(TradingContract):
    """Short-locate/hard-to-borrow evidence consumed from data or risk feeds.

    Attributes:
        symbol: Instrument symbol.
        available_shares: Locate-authorized available share quantity.
        hard_to_borrow: Whether the instrument is classified hard-to-borrow.
        source: Evidence source identifier.
        freshness_age_ms: Evidence age in milliseconds at validation time.
        ttl_ms: Configured freshness time-to-live in milliseconds.
    """

    symbol: str
    available_shares: Decimal = Field(ge=0)
    hard_to_borrow: bool = False
    source: str
    freshness_age_ms: int = Field(ge=0)
    ttl_ms: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_locate_snapshot(self) -> LocateSnapshot:
        """Validate locate snapshot identifiers.

        Returns:
            LocateSnapshot: Validated locate snapshot.

        Raises:
            ValueError: If symbol or source are blank.
        """
        logger.info("Validating locate snapshot for {}.", self.symbol)
        if not self.symbol.strip() or not self.source.strip():
            raise ValueError("symbol and source must be non-empty.")
        return self

    def is_fresh(self) -> bool:
        """Return whether the locate snapshot is within its TTL.

        Returns:
            bool: True when the snapshot has not exceeded its TTL.
        """
        logger.debug(
            "Checking locate snapshot freshness age={} ttl={}.",
            self.freshness_age_ms,
            self.ttl_ms,
        )
        return self.freshness_age_ms <= self.ttl_ms


class DefenseInDepthRailLimits(TradingContract):
    """Static, un-overridable defense-in-depth rail ceilings (TRD-FR-048).

    Attributes:
        max_mutation_attempts_per_window: Maximum mutation attempts allowed
            per rolling window for one (account, symbol) pair.
        window_seconds: Rolling window duration in seconds.
        max_open_positions: Maximum simultaneous open positions per account.
        daily_notional_ceiling: Cumulative daily account-currency notional
            ceiling, reset at a configured session boundary.
    """

    max_mutation_attempts_per_window: int = Field(gt=0)
    window_seconds: int = Field(gt=0)
    max_open_positions: int = Field(gt=0)
    daily_notional_ceiling: Decimal = Field(ge=0)


class DailyRailState(TradingContract):
    """Mutable rail counters supplied by the caller for one evaluation.

    Attributes:
        mutation_attempts_in_window: Mutation attempts observed in the
            current rolling window for this (account, symbol) pair.
        open_positions_count: Currently open positions for this account.
        cumulative_daily_notional: Cumulative notional already consumed in
            the current daily window, in account currency.
    """

    mutation_attempts_in_window: int = Field(ge=0)
    open_positions_count: int = Field(ge=0)
    cumulative_daily_notional: Decimal = Field(ge=0)


class OrderIntent(TradingContract):
    """Local, broker-independent order parameter intent.

    Attributes:
        symbol: Instrument symbol.
        side: Trade direction.
        order_type: Local order type classification.
        volume: Requested order volume.
        price: Limit/stop trigger price. Required for pending order types.
        stop_limit_price: Stop-limit resting price. Required for
            ``stop_limit`` orders.
        sl: Optional stop-loss price.
        tp: Optional take-profit price.
        max_slippage_points: Maximum acceptable slippage in points. Required
            for market orders (TRD-FR-044).
        tif: Requested time-in-force.
        expiration: Expiration timestamp, required when ``tif`` is ``GTD``.
        is_short: Whether this intent represents a short-sale.
    """

    symbol: str
    side: OrderSide
    order_type: OrderType
    volume: Decimal = Field(gt=0)
    price: Decimal | None = None
    stop_limit_price: Decimal | None = None
    sl: Decimal | None = None
    tp: Decimal | None = None
    max_slippage_points: int | None = Field(default=None, ge=0)
    tif: TimeInForce = TimeInForce.GTC
    expiration: str | None = None
    is_short: bool = False

    @model_validator(mode="after")
    def validate_intent(self) -> OrderIntent:
        """Validate structural order intent completeness.

        Returns:
            OrderIntent: Validated order intent.

        Raises:
            ValueError: If symbol is blank, a pending order type is missing
                its trigger price, a stop-limit order is missing its resting
                price, or a GTD order is missing an expiration.
        """
        logger.info(
            "Validating order intent structure for {} {} {}.",
            self.symbol,
            self.side.value,
            self.order_type.value,
        )
        if not self.symbol.strip():
            raise ValueError("symbol must be non-empty.")
        if self.order_type in PENDING_ORDER_TYPES and self.price is None:
            raise ValueError("price is required for pending order types.")
        if self.order_type is OrderType.STOP_LIMIT and self.stop_limit_price is None:
            raise ValueError("stop_limit_price is required for stop_limit orders.")
        if self.tif is TimeInForce.GTD and not (self.expiration or "").strip():
            raise ValueError("expiration is required when tif is GTD.")
        return self


class OrderValidationContext(TradingContract):
    """Evidence bundle required to validate one order intent.

    Attributes:
        route: Requested runtime route.
        reference_price: Current market reference price for the symbol.
        constraints: Dynamically resolved symbol trading constraints.
        account_margin: Account margin evidence.
        conversion_rate: Optional conversion-rate evidence, required only
            when the instrument quote currency differs from the account
            currency.
        market_session: Optional trading-calendar session evidence.
        supported_tif: Broker-supported time-in-force values.
        fat_finger_ceiling: Immutable notional ceiling in account currency.
        rail_limits: Defense-in-depth rail ceilings.
        rail_state: Current defense-in-depth rail counters.
        locate: Optional short-locate evidence, required for short intents.
    """

    route: TradingRoute
    reference_price: Decimal = Field(gt=0)
    constraints: SymbolTradingConstraints
    account_margin: AccountMarginContext
    conversion_rate: ConversionRateEvidence | None = None
    market_session: MarketSessionEvidence | None = None
    supported_tif: tuple[TimeInForce, ...] = Field(default=DEFAULT_SUPPORTED_TIF)
    fat_finger_ceiling: Decimal = Field(ge=0)
    rail_limits: DefenseInDepthRailLimits
    rail_state: DailyRailState
    locate: LocateSnapshot | None = None


class OrderValidationResult(TradingContract):
    """Validated and normalized order intent plus the audit trail.

    Attributes:
        normalized_intent: JSON-safe normalized order intent.
        audit: JSON-safe combined validation audit record.
    """

    normalized_intent: JsonObject
    audit: JsonObject


def normalize_decimal_to_step(
    value: Decimal, *, step: Decimal, rounding: str
) -> Decimal:
    """Normalize a Decimal value to the nearest instrument step.

    Args:
        value: Raw value to normalize.
        step: Instrument step size (volume step or tick size).
        rounding: ``decimal`` rounding mode (e.g. ``ROUND_DOWN``).

    Returns:
        Decimal: Step-aligned normalized value.
    """
    logger.debug("Normalizing {} to step {} using {}.", value, step, rounding)
    quantized_units = (value / step).to_integral_value(rounding=rounding)
    return quantized_units * step


def normalize_volume(
    volume: Decimal,
    *,
    constraints: SymbolTradingConstraints,
    allow_round_up: bool = False,
) -> tuple[Decimal, Decimal]:
    """Normalize requested volume to the symbol's volume step.

    Rounds down unless explicitly authorized by policy (TRD-FR-039).

    Args:
        volume: Requested raw volume.
        constraints: Symbol trading constraints.
        allow_round_up: Whether policy explicitly authorizes rounding up.

    Returns:
        tuple[Decimal, Decimal]: Original and normalized volume values.
    """
    logger.info("Normalizing volume {} for {}.", volume, constraints.symbol)
    rounding = ROUND_UP if allow_round_up else ROUND_DOWN
    normalized = normalize_decimal_to_step(
        volume, step=constraints.volume_step, rounding=rounding
    )
    return volume, normalized


def normalize_stop_price(
    value: Decimal,
    *,
    tick_size: Decimal,
    below_market: bool,
) -> tuple[Decimal, Decimal]:
    """Normalize a stop price to the tick size, rounding away from market.

    Direction-aware rounding never moves a stop closer to the current market
    price than requested, preserving minimum-distance safety (TRD-FR-039).

    Args:
        value: Raw requested stop price.
        tick_size: Symbol tick size.
        below_market: Whether this stop sits below the current market price.

    Returns:
        tuple[Decimal, Decimal]: Original and normalized stop price values.
    """
    logger.debug("Normalizing stop price {} below_market={}.", value, below_market)
    rounding = ROUND_DOWN if below_market else ROUND_UP
    normalized = normalize_decimal_to_step(value, step=tick_size, rounding=rounding)
    return value, normalized


def compute_account_currency_notional(
    *,
    volume: Decimal,
    reference_price: Decimal,
    constraints: SymbolTradingConstraints,
    account_currency: str,
    conversion: ConversionRateEvidence | None,
) -> tuple[Decimal, Decimal | None]:
    """Compute order notional value expressed in account currency.

    Args:
        volume: Order volume.
        reference_price: Current market reference price.
        constraints: Symbol trading constraints.
        account_currency: Account base currency.
        conversion: Optional conversion-rate evidence.

    Returns:
        tuple[Decimal, Decimal | None]: Account-currency notional and the
        conversion rate used, if any.

    Raises:
        TradingValidationError: If the instrument quote currency differs
            from the account currency and no fresh, matching conversion-rate
            evidence is supplied.
    """
    logger.info(
        "Computing account-currency notional for {} volume={}.",
        constraints.symbol,
        volume,
    )
    quote_notional = volume * constraints.contract_size * reference_price
    if constraints.quote_currency == account_currency:
        return quote_notional, None

    if conversion is None or not conversion.is_fresh():
        raise TradingValidationError(
            "Missing or stale conversion-rate evidence for non-account-currency "
            "notional computation.",
            details={
                "symbol": constraints.symbol,
                "quote_currency": constraints.quote_currency,
                "account_currency": account_currency,
            },
        )
    if (
        conversion.from_currency != constraints.quote_currency
        or conversion.to_currency != account_currency
    ):
        raise TradingValidationError(
            "Conversion-rate evidence currency pair does not match the order.",
            details={
                "symbol": constraints.symbol,
                "expected_pair": f"{constraints.quote_currency}->{account_currency}",
                "evidence_pair": (
                    f"{conversion.from_currency}->{conversion.to_currency}"
                ),
            },
        )
    return quote_notional * conversion.rate, conversion.rate


def validate_volume(
    volume: Decimal,
    *,
    constraints: SymbolTradingConstraints,
) -> JsonObject:
    """Validate requested volume against dynamic symbol constraints.

    Args:
        volume: Requested order volume.
        constraints: Symbol trading constraints.

    Returns:
        JsonObject: Validation audit record.

    Raises:
        TradingValidationError: If volume violates min, max, or step rules.
    """
    logger.info("Validating volume {} for {}.", volume, constraints.symbol)
    if volume < constraints.volume_min or volume > constraints.volume_max:
        raise TradingValidationError(
            "Volume is outside the symbol's min/max bounds.",
            details={
                "symbol": constraints.symbol,
                "volume": str(volume),
                "volume_min": str(constraints.volume_min),
                "volume_max": str(constraints.volume_max),
            },
        )
    remainder = volume % constraints.volume_step
    if remainder != 0:
        raise TradingValidationError(
            "Volume does not align with the symbol's volume step.",
            details={
                "symbol": constraints.symbol,
                "volume": str(volume),
                "volume_step": str(constraints.volume_step),
            },
        )
    logger.debug("Volume {} passed min/max/step validation.", volume)
    return {"volume": str(volume), "volume_step": str(constraints.volume_step)}


def validate_stops(
    *,
    side: OrderSide,
    sl: Decimal | None,
    tp: Decimal | None,
    reference_price: Decimal,
    constraints: SymbolTradingConstraints,
) -> JsonObject:
    """Validate direction-aware stop-loss/take-profit geometry.

    Args:
        side: Trade direction.
        sl: Optional stop-loss price.
        tp: Optional take-profit price.
        reference_price: Current market reference price.
        constraints: Symbol trading constraints.

    Returns:
        JsonObject: Validation audit record.

    Raises:
        TradingValidationError: If a stop is on the wrong side of the market
            or violates the minimum stop distance.
    """
    logger.info("Validating stop geometry for {} {}.", constraints.symbol, side.value)
    audit: JsonObject = {}
    is_buy = side is OrderSide.BUY
    if sl is not None:
        sl_below_market = sl < reference_price
        if sl_below_market != is_buy:
            raise TradingValidationError(
                "Stop-loss is on the wrong side of the market for this side.",
                details={
                    "symbol": constraints.symbol,
                    "side": side.value,
                    "sl": str(sl),
                },
            )
        distance = abs(reference_price - sl)
        if distance < constraints.min_stop_distance:
            raise TradingValidationError(
                "Stop-loss violates the minimum stop distance.",
                details={
                    "symbol": constraints.symbol,
                    "distance": str(distance),
                    "min_stop_distance": str(constraints.min_stop_distance),
                },
            )
        audit["sl_distance"] = str(distance)
    if tp is not None:
        tp_above_market = tp > reference_price
        if tp_above_market != is_buy:
            raise TradingValidationError(
                "Take-profit is on the wrong side of the market for this side.",
                details={
                    "symbol": constraints.symbol,
                    "side": side.value,
                    "tp": str(tp),
                },
            )
        distance = abs(tp - reference_price)
        if distance < constraints.min_stop_distance:
            raise TradingValidationError(
                "Take-profit violates the minimum stop distance.",
                details={
                    "symbol": constraints.symbol,
                    "distance": str(distance),
                    "min_stop_distance": str(constraints.min_stop_distance),
                },
            )
        audit["tp_distance"] = str(distance)
    logger.debug("Stop geometry audit for {}: {}.", constraints.symbol, audit)
    return audit


def validate_margin(
    *,
    volume: Decimal,
    reference_price: Decimal,
    constraints: SymbolTradingConstraints,
    account: AccountMarginContext,
    conversion: ConversionRateEvidence | None,
) -> JsonObject:
    """Validate that free margin covers the trade intent's margin requirement.

    Args:
        volume: Requested order volume.
        reference_price: Current market reference price.
        constraints: Symbol trading constraints.
        account: Account margin evidence.
        conversion: Optional conversion-rate evidence.

    Returns:
        JsonObject: Validation audit record.

    Raises:
        TradingValidationError: If required margin exceeds free margin.
    """
    logger.info("Validating margin sufficiency for {}.", constraints.symbol)
    notional, rate_used = compute_account_currency_notional(
        volume=volume,
        reference_price=reference_price,
        constraints=constraints,
        account_currency=account.account_currency,
        conversion=conversion,
    )
    required_margin = notional / Decimal(account.leverage)
    if required_margin > account.free_margin:
        raise TradingValidationError(
            "Insufficient free margin for the requested trade intent.",
            details={
                "symbol": constraints.symbol,
                "required_margin": str(required_margin),
                "free_margin": str(account.free_margin),
            },
        )
    logger.debug(
        "Margin check passed for {}: required={} free={}.",
        constraints.symbol,
        required_margin,
        account.free_margin,
    )
    return {
        "required_margin": str(required_margin),
        "conversion_rate_used": str(rate_used) if rate_used is not None else None,
    }


def validate_market_session(
    *,
    route: TradingRoute,
    symbol: str,
    evidence: MarketSessionEvidence | None,
) -> JsonObject:
    """Validate instrument trading session availability.

    Fails closed if session evidence is missing or expired in live-sensitive
    routes (TRD-FR-042, TRD-XM-003).

    Args:
        route: Requested runtime route.
        symbol: Instrument symbol.
        evidence: Optional market session evidence.

    Returns:
        JsonObject: Validation audit record.

    Raises:
        TradingValidationError: If evidence is missing/stale for a
            live-sensitive route, mismatched to the symbol, or the session
            is closed.
    """
    logger.info("Validating market session for {} on route {}.", symbol, route.value)
    live_sensitive = route in LIVE_SENSITIVE_ROUTES
    if evidence is None:
        if live_sensitive:
            raise TradingValidationError(
                "Market session evidence is required for live-sensitive routes.",
                details={"symbol": symbol, "route": route.value},
            )
        logger.debug(
            "Skipping session evidence check for non-live route {}.", route.value
        )
        return {"session_checked": False}
    if evidence.symbol != symbol:
        raise TradingValidationError(
            "Market session evidence symbol does not match the order.",
            details={"symbol": symbol, "evidence_symbol": evidence.symbol},
        )
    if live_sensitive and not evidence.is_fresh():
        raise TradingValidationError(
            "Market session evidence is stale.",
            details={
                "symbol": symbol,
                "freshness_age_ms": evidence.freshness_age_ms,
                "ttl_ms": evidence.ttl_ms,
            },
        )
    if not evidence.is_open:
        raise TradingValidationError(
            "Instrument trading session is closed.",
            details={"symbol": symbol, "source": evidence.source},
        )
    logger.debug("Market session for {} is open and fresh.", symbol)
    return {"session_checked": True, "source": evidence.source}


def validate_time_in_force(
    *,
    tif: TimeInForce,
    supported: tuple[TimeInForce, ...],
) -> JsonObject:
    """Validate that the requested TIF is supported by broker capabilities.

    Args:
        tif: Requested time-in-force.
        supported: Broker-supported time-in-force values.

    Returns:
        JsonObject: Validation audit record.

    Raises:
        TradingValidationError: If the TIF is not in the supported set.
    """
    logger.info("Validating time-in-force {}.", tif.value)
    if tif not in supported:
        raise TradingValidationError(
            "Time-in-force is not supported by broker capability profile.",
            details={"tif": tif.value, "supported": [item.value for item in supported]},
        )
    logger.debug("Time-in-force {} is supported.", tif.value)
    return {"tif": tif.value}


def validate_execution_protections(
    *,
    order_type: OrderType,
    max_slippage_points: int | None,
    price: Decimal | None,
    reference_price: Decimal,
    price_collar_bps: Decimal,
) -> JsonObject:
    """Validate mandatory slippage protection and pending-order price collars.

    Args:
        order_type: Local order type classification.
        max_slippage_points: Maximum acceptable slippage in points.
        price: Pending order trigger price.
        reference_price: Current market reference price.
        price_collar_bps: Allowed price deviation in basis points.

    Returns:
        JsonObject: Validation audit record.

    Raises:
        TradingValidationError: If a market order lacks defined slippage
            protection, or a pending order price is outside its collar.
    """
    logger.info("Validating execution protections for {}.", order_type.value)
    if order_type is OrderType.MARKET:
        if max_slippage_points is None:
            raise TradingValidationError(
                "Market orders must define maximum acceptable slippage.",
                details={"order_type": order_type.value},
            )
        return {"max_slippage_points": max_slippage_points}

    if price is None:
        raise TradingMappedError(
            "Pending orders require a trigger price for collar validation.",
            code="INVALID_INPUT",
            details={"order_type": order_type.value},
        )
    collar_width = reference_price * price_collar_bps / BPS_DENOMINATOR
    deviation = abs(price - reference_price)
    if deviation > collar_width:
        raise TradingValidationError(
            "Pending order price is outside the dynamic price collar.",
            details={
                "order_type": order_type.value,
                "price": str(price),
                "reference_price": str(reference_price),
                "collar_width": str(collar_width),
            },
        )
    logger.debug("Pending order price collar check passed for {}.", order_type.value)
    return {"collar_width": str(collar_width), "deviation": str(deviation)}


def validate_fat_finger_ceiling(
    *,
    volume: Decimal,
    reference_price: Decimal,
    constraints: SymbolTradingConstraints,
    account_currency: str,
    conversion: ConversionRateEvidence | None,
    ceiling: Decimal,
) -> JsonObject:
    """Validate the immutable fat-finger notional ceiling (TRD-FR-045/047).

    Args:
        volume: Requested order volume.
        reference_price: Current market reference price.
        constraints: Symbol trading constraints.
        account_currency: Account base currency.
        conversion: Optional conversion-rate evidence.
        ceiling: Immutable notional ceiling in account currency.

    Returns:
        JsonObject: Validation audit record with notional, conversion rate,
        and ceiling.

    Raises:
        TradingValidationError: If notional exceeds the ceiling.
    """
    logger.info("Validating fat-finger ceiling for {}.", constraints.symbol)
    notional, rate_used = compute_account_currency_notional(
        volume=volume,
        reference_price=reference_price,
        constraints=constraints,
        account_currency=account_currency,
        conversion=conversion,
    )
    if notional > ceiling:
        raise TradingValidationError(
            "Order notional exceeds the immutable fat-finger ceiling.",
            details={
                "symbol": constraints.symbol,
                "notional": str(notional),
                "ceiling": str(ceiling),
            },
        )
    logger.debug(
        "Fat-finger ceiling check passed for {}: notional={} ceiling={}.",
        constraints.symbol,
        notional,
        ceiling,
    )
    return {
        "notional": str(notional),
        "ceiling": str(ceiling),
        "conversion_rate_used": str(rate_used) if rate_used is not None else None,
    }


def validate_defense_in_depth_rails(
    *,
    notional: Decimal,
    limits: DefenseInDepthRailLimits,
    state: DailyRailState,
) -> JsonObject:
    """Validate the static defense-in-depth rails (TRD-FR-048).

    These rails are deliberately crude last-line protections and must not
    grow into risk logic (position sizing, exposure modeling).

    Args:
        notional: Account-currency notional for this order.
        limits: Defense-in-depth rail ceilings.
        state: Current defense-in-depth rail counters.

    Returns:
        JsonObject: Validation audit record.

    Raises:
        TradingValidationError: If any rail ceiling would be breached.
    """
    logger.info("Validating defense-in-depth rails for notional {}.", notional)
    if state.mutation_attempts_in_window >= limits.max_mutation_attempts_per_window:
        raise TradingValidationError(
            "Mutation attempt rail exceeded for the rolling window.",
            details={
                "attempts": state.mutation_attempts_in_window,
                "limit": limits.max_mutation_attempts_per_window,
            },
        )
    if state.open_positions_count >= limits.max_open_positions:
        raise TradingValidationError(
            "Open position count rail exceeded.",
            details={
                "open_positions": state.open_positions_count,
                "limit": limits.max_open_positions,
            },
        )
    projected_daily_notional = state.cumulative_daily_notional + notional
    if projected_daily_notional > limits.daily_notional_ceiling:
        raise TradingValidationError(
            "Cumulative daily notional rail exceeded.",
            details={
                "projected_daily_notional": str(projected_daily_notional),
                "ceiling": str(limits.daily_notional_ceiling),
            },
        )
    logger.debug("Defense-in-depth rails passed for notional {}.", notional)
    return {"projected_daily_notional": str(projected_daily_notional)}


def validate_short_locate(
    *,
    is_short: bool,
    locate: LocateSnapshot | None,
) -> JsonObject:
    """Validate short-sale locate/hard-to-borrow authorization (TRD-FR-049).

    Args:
        is_short: Whether this order intent is a short-sale.
        locate: Optional locate snapshot evidence.

    Returns:
        JsonObject: Validation audit record.

    Raises:
        TradingValidationError: If short and no valid, fresh locate with
            available shares is present.
    """
    logger.info("Validating short-locate requirement, is_short={}.", is_short)
    if not is_short:
        logger.debug("Order is not a short-sale; skipping locate check.")
        return {"locate_required": False}
    if locate is None or not locate.is_fresh() or locate.available_shares <= 0:
        raise TradingValidationError(
            "Short-sale locate/HTB authorization is missing, stale, or unavailable.",
            details={"locate_present": locate is not None},
        )
    logger.debug("Short-locate authorization confirmed for {}.", locate.symbol)
    return {"locate_required": True, "available_shares": str(locate.available_shares)}


def validate_order_request(
    intent: OrderIntent,
    *,
    context: OrderValidationContext,
) -> OrderValidationResult:
    """Combine all local order parameter validations (TRD-FR-046).

    Runs normalization and every sub-validation in sequence, short-circuiting
    on the first failure by propagating the corresponding structured
    ``VALIDATION_FAILED`` or ``INVALID_INPUT`` exception.

    Args:
        intent: Local order parameter intent.
        context: Evidence bundle required to validate the intent.

    Returns:
        OrderValidationResult: Normalized intent and combined audit trail.

    Raises:
        TradingValidationError: If any sub-validation fails.
        TradingMappedError: If required structural input is missing.
    """
    logger.info(
        "Validating order request for {} {} {}.",
        intent.symbol,
        intent.side.value,
        intent.order_type.value,
    )
    if intent.symbol != context.constraints.symbol:
        raise TradingMappedError(
            "Order intent symbol does not match validation context constraints.",
            code="INVALID_INPUT",
            details={
                "intent_symbol": intent.symbol,
                "constraints_symbol": context.constraints.symbol,
            },
        )

    audit: JsonObject = {}
    _, normalized_volume = normalize_volume(
        intent.volume, constraints=context.constraints
    )
    audit["volume"] = {
        "original": str(intent.volume),
        "normalized": str(normalized_volume),
    }
    audit["volume_check"] = validate_volume(
        normalized_volume, constraints=context.constraints
    )

    normalized_sl = intent.sl
    if normalized_sl is not None:
        _, normalized_sl = normalize_stop_price(
            normalized_sl,
            tick_size=context.constraints.tick_size,
            below_market=normalized_sl < context.reference_price,
        )
    normalized_tp = intent.tp
    if normalized_tp is not None:
        _, normalized_tp = normalize_stop_price(
            normalized_tp,
            tick_size=context.constraints.tick_size,
            below_market=normalized_tp < context.reference_price,
        )
    audit["stops_check"] = validate_stops(
        side=intent.side,
        sl=normalized_sl,
        tp=normalized_tp,
        reference_price=context.reference_price,
        constraints=context.constraints,
    )
    audit["margin_check"] = validate_margin(
        volume=normalized_volume,
        reference_price=context.reference_price,
        constraints=context.constraints,
        account=context.account_margin,
        conversion=context.conversion_rate,
    )
    audit["session_check"] = validate_market_session(
        route=context.route,
        symbol=intent.symbol,
        evidence=context.market_session,
    )
    audit["tif_check"] = validate_time_in_force(
        tif=intent.tif,
        supported=context.supported_tif,
    )
    audit["execution_protections_check"] = validate_execution_protections(
        order_type=intent.order_type,
        max_slippage_points=intent.max_slippage_points,
        price=intent.price,
        reference_price=context.reference_price,
        price_collar_bps=context.constraints.price_collar_bps,
    )
    audit["fat_finger_check"] = validate_fat_finger_ceiling(
        volume=normalized_volume,
        reference_price=context.reference_price,
        constraints=context.constraints,
        account_currency=context.account_margin.account_currency,
        conversion=context.conversion_rate,
        ceiling=context.fat_finger_ceiling,
    )
    notional, _ = compute_account_currency_notional(
        volume=normalized_volume,
        reference_price=context.reference_price,
        constraints=context.constraints,
        account_currency=context.account_margin.account_currency,
        conversion=context.conversion_rate,
    )
    audit["rails_check"] = validate_defense_in_depth_rails(
        notional=notional,
        limits=context.rail_limits,
        state=context.rail_state,
    )
    audit["short_locate_check"] = validate_short_locate(
        is_short=intent.is_short,
        locate=context.locate,
    )

    normalized_intent = intent.model_dump(mode="json")
    normalized_intent["volume"] = str(normalized_volume)
    normalized_intent["sl"] = str(normalized_sl) if normalized_sl is not None else None
    normalized_intent["tp"] = str(normalized_tp) if normalized_tp is not None else None
    normalized_intent["price"] = str(intent.price) if intent.price is not None else None
    normalized_intent["stop_limit_price"] = (
        str(intent.stop_limit_price) if intent.stop_limit_price is not None else None
    )
    logger.info("Order request validation passed for {}.", intent.symbol)
    return OrderValidationResult(normalized_intent=normalized_intent, audit=audit)
