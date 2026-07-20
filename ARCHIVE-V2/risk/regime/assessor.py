"""Market regime assessment engine.

Responsible for spread z-score thresholds, rolling volatility
classification, stale quote checks, session status, rollover
blackout windows, and calendar news matching.
"""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from app.services.risk.models import (
    MarketRiskSnapshot,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    RiskReasonCode,
)
from app.services.risk.policy.contracts import EffectiveRiskPolicy
from app.utils.logger import logger
from app.utils.normalization import parse_datetime, to_utc_datetime, utc_now
from pydantic import Field

if TYPE_CHECKING:
    from app.services.risk.validations import ValidationResult


class RiskRegime(StrEnum):
    """Overall synthesized market regime classification."""

    NORMAL = "normal"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    WIDE_SPREAD = "wide_spread"
    ILLIQUID = "illiquid"
    NEWS_BLACKOUT = "news_blackout"
    ROLLOVER_BLACKOUT = "rollover_blackout"
    MARKET_CLOSED = "market_closed"
    STALE_DATA = "stale_data"
    SUSPENDED = "suspended"
    INVALID_QUOTE = "invalid_quote"
    UNKNOWN = "unknown"


class SpreadRegime(StrEnum):
    """Spread widening classification."""

    NORMAL = "normal"
    WIDE = "wide"
    EXTREME = "extreme"


class VolatilityRegime(StrEnum):
    """Volatility classification."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    SPIKE = "spike"


class LiquidityRegime(StrEnum):
    """Liquidity classification based on quotes/ticks."""

    NORMAL = "normal"
    THIN = "thin"
    ILLIQUID = "illiquid"


class NewsRegime(StrEnum):
    """News impact/blackout classification."""

    NORMAL = "normal"
    HIGH_IMPACT = "high_impact"
    BLACKOUT = "blackout"


class SessionRegime(StrEnum):
    """Market session status classification."""

    CLOSED = "closed"
    ACTIVE = "active"


class RolloverRegime(StrEnum):
    """Broker rollover blackout status classification."""

    NORMAL = "normal"
    BLACKOUT = "blackout"


class SpreadSigmaThresholds(RiskContract):
    """Thresholds for spread z-score classification."""

    threshold_normal: Decimal = Field(
        default=Decimal("1.5"),
        description="Z-score threshold for wide spread classification.",
    )
    threshold_wide: Decimal = Field(
        default=Decimal("3.0"),
        description="Z-score threshold for extreme spread classification.",
    )


class VolatilityThresholds(RiskContract):
    """Multipliers for volatility ratio classification."""

    spike_multiplier: Decimal = Field(
        default=Decimal("2.0"),
        description="Multiplier for volatility spike classification.",
    )
    high_multiplier: Decimal = Field(
        default=Decimal("1.3"),
        description="Multiplier for high volatility classification.",
    )
    low_multiplier: Decimal = Field(
        default=Decimal("0.5"),
        description="Multiplier for low volatility classification.",
    )


class RegimeAssessment(RiskContract):
    """Contract representing the outcome of a market regime assessment."""

    regime: RiskRegime = Field(..., description="Overall synthesized market regime.")
    spread_regime: SpreadRegime = Field(
        ..., description="Spread regime classification."
    )
    volatility_regime: VolatilityRegime = Field(
        ..., description="Volatility regime classification."
    )
    liquidity_regime: LiquidityRegime = Field(
        ..., description="Liquidity regime classification."
    )
    news_regime: NewsRegime = Field(..., description="News regime classification.")
    session_regime: SessionRegime = Field(
        ..., description="Session regime classification."
    )
    rollover_regime: RolloverRegime = Field(
        ..., description="Rollover regime classification."
    )
    status: RiskDecisionStatus = Field(..., description="Decision status outcome.")
    reason: str = Field(..., description="Human-readable reason for the decision.")
    reason_code: RiskReasonCode = Field(..., description="Stable reason code.")
    timestamp: datetime = Field(..., description="Assessment timestamp.")


RegimeResult = RegimeAssessment


def _compute_stats(values: list[Decimal]) -> tuple[Decimal, Decimal]:
    """Compute mean and standard deviation of Decimal values.

    Args:
        values: List of Decimal values to compute statistics for.

    Returns:
        tuple[Decimal, Decimal]: The calculated mean and standard deviation.
    """
    logger.debug("Computing stats for %d values.", len(values))
    if not values:
        return Decimal(0), Decimal(0)
    n = len(values)
    float_vals = [float(v) for v in values]
    mean_val = sum(float_vals) / n
    variance = sum((x - mean_val) ** 2 for x in float_vals) / n
    std_val = math.sqrt(variance)
    return Decimal(str(mean_val)), Decimal(str(std_val))


def _calculate_rolling_vol(prices: list[Decimal], lookback: int) -> Decimal:
    """Calculate volatility (std of log returns) over lookback window.

    Args:
        prices: List of prices to calculate rolling volatility on.
        lookback: Number of periods to look back.

    Returns:
        Decimal: Calculated standard deviation of log returns.
    """
    logger.debug("Calculating rolling volatility for lookback=%d", lookback)
    if len(prices) <= lookback:
        return Decimal(0)
    # Take the last lookback + 1 prices to get lookback returns
    subset = prices[-(lookback + 1) :]
    returns = []
    for i in range(1, len(subset)):
        p1 = float(subset[i - 1])
        p2 = float(subset[i])
        if p1 <= 0 or p2 <= 0:
            returns.append(Decimal(0))
        else:
            returns.append(Decimal(str(math.log(p2 / p1))))
    _, std = _compute_stats(returns)
    return std


def classify_spread_regime(
    spread: Decimal,
    sigma: Decimal,
    thresholds: SpreadSigmaThresholds,
    mean: Decimal = Decimal(0),
) -> SpreadRegime:
    """Classifies spread-to-volatility condition based on z-score.

    Args:
        spread: The current market spread.
        sigma: Standard deviation of spreads.
        thresholds: The SpreadSigmaThresholds settings.
        mean: Mean spread. Defaults to 0.

    Returns:
        SpreadRegime: Classified spread regime.
    """
    logger.debug(
        "Classifying spread regime (spread=%s, sigma=%s, mean=%s)",
        spread,
        sigma,
        mean,
    )
    if sigma <= 0:
        logger.debug("Sigma is <= 0; returning SpreadRegime.NORMAL")
        return SpreadRegime.NORMAL

    z_score = abs(spread - mean) / sigma
    if z_score <= thresholds.threshold_normal:
        return SpreadRegime.NORMAL
    if z_score <= thresholds.threshold_wide:
        return SpreadRegime.WIDE
    return SpreadRegime.EXTREME


def classify_volatility_regime(
    short_sigma: Decimal,
    medium_sigma: Decimal,
    long_sigma: Decimal,
    thresholds: VolatilityThresholds,
) -> VolatilityRegime:
    """Classifies volatility state based on rolling sigma metrics.

    Args:
        short_sigma: Short-term rolling volatility.
        medium_sigma: Medium-term rolling volatility.
        long_sigma: Long-term rolling volatility.
        thresholds: VolatilityThresholds multipliers.

    Returns:
        VolatilityRegime: Classified volatility regime.
    """
    logger.debug(
        "Classifying volatility regime (short=%s, med=%s, long=%s)",
        short_sigma,
        medium_sigma,
        long_sigma,
    )
    if long_sigma <= 0:
        res = (
            VolatilityRegime.LOW
            if short_sigma == Decimal(0)
            else VolatilityRegime.SPIKE
        )
        logger.debug("Long sigma is <= 0; classified as %s", res)
        return res

    ratio = short_sigma / long_sigma
    ratio_med = short_sigma / medium_sigma if medium_sigma > 0 else ratio

    if ratio >= thresholds.spike_multiplier or ratio_med >= thresholds.spike_multiplier:
        return VolatilityRegime.SPIKE
    if ratio >= thresholds.high_multiplier:
        return VolatilityRegime.HIGH
    if ratio <= thresholds.low_multiplier:
        return VolatilityRegime.LOW
    return VolatilityRegime.NORMAL


def is_rollover_blackout(
    server_time: datetime,
    policy: EffectiveRiskPolicy,
    market_context: dict[str, Any] | None = None,
) -> bool:
    """Evaluates broker-midnight rollover blackout boundaries from UTC configuration.

    Args:
        server_time: Current UTC server time.
        policy: EffectiveRiskPolicy containing resolved config.
        market_context: Optional context dictionary for overrides.

    Returns:
        bool: True if time is within the rollover blackout window.
    """
    logger.debug("Checking rollover blackout for server_time=%s", server_time)
    config = policy.resolved_config
    ctx = market_context or {}

    start_str = ctx.get(
        "rollover_blackout_start_utc",
        getattr(config, "rollover_blackout_start_utc", None),
    )
    end_str = ctx.get(
        "rollover_blackout_end_utc",
        getattr(config, "rollover_blackout_end_utc", None),
    )
    if not start_str or not end_str:
        logger.debug("Rollover start/end times not configured; returning False")
        return False

    try:
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
    except ValueError as e:
        logger.warning(
            "Error parsing rollover config times (%s, %s): %s",
            start_str,
            end_str,
            e,
        )
        return False

    now_mins = server_time.hour * 60 + server_time.minute
    start_mins = sh * 60 + sm
    end_mins = eh * 60 + em

    if start_mins <= end_mins:
        res = start_mins <= now_mins <= end_mins
    else:
        # Overnight window, e.g. 23:50 to 00:10
        res = now_mins >= start_mins or now_mins <= end_mins

    logger.debug("Rollover blackout check result: %s", res)
    return res


def validate_market_freshness(
    market: MarketRiskSnapshot,
    _policy: EffectiveRiskPolicy,
    now_utc: datetime,
    market_context: dict[str, Any] | None = None,
) -> ValidationResult:
    """Detects stale or inconsistent market evidence.

    Args:
        market: The MarketRiskSnapshot to validate.
        policy: The EffectiveRiskPolicy containing resolved configuration.
        now_utc: Current UTC datetime.
        market_context: Optional context dict containing max_stale_seconds override.

    Returns:
        ValidationResult: The validation result outcome.
    """
    logger.debug("Validating market freshness.")
    ctx = market_context or {}

    freshness = to_utc_datetime(market.freshness)
    age_seconds = (now_utc - freshness).total_seconds()

    # Default max quote age is 60 seconds
    max_age = float(ctx.get("max_stale_seconds", 60.0))
    if age_seconds > max_age:
        msg = f"Market data is stale. Age: {age_seconds:.1f}s (max: {max_age:.1f}s)"
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "STALE_EVIDENCE",
            "details": {"age_seconds": age_seconds, "max_age": max_age},
        }

    return {
        "valid": True,
        "message": "Market data is fresh.",
        "code": "OK",
        "details": {},
    }


class RegimeRiskEngine:
    """Facade for deterministic regime evaluation.

    Pure when snapshots and policies/configs are supplied.
    """

    def __init__(self, config: RiskConfig) -> None:
        """Initialize engine with active risk config.

        Args:
            config: The active RiskConfig profile.
        """
        logger.info("Initializing RegimeRiskEngine.")
        self.config = config

    def assess(
        self,
        market_snapshot: MarketRiskSnapshot,
        calendar_evidence: list[dict[str, Any]],
        market_context: dict[str, Any],
        now_utc: datetime | None = None,
    ) -> RegimeAssessment:
        """Assess all market regime components and determine decision status.

        Args:
            market_snapshot: Current market snapshot.
            calendar_evidence: List of upcoming news/calendar event dictionaries.
            market_context: Context inputs containing spread/price history.
            now_utc: Optional override for current UTC time.

        Returns:
            RegimeAssessment: The resolved market regimes and risk status block.
        """
        now = now_utc or utc_now()
        logger.info("Assessing market regime at %s", now)

        # 1. Input validation using validation.py helper
        from app.services.risk.regime.validation import validate_regime_inputs

        val_res = validate_regime_inputs(market_snapshot)
        if not val_res["valid"]:
            return self._build_error_result(
                RiskRegime.INVALID_QUOTE,
                RiskReasonCode.INVALID_INPUT,
                val_res["message"],
                now,
            )

        # 1.5. Detect gap events from historical prices
        gap_event = market_context.get("gap_event", False)
        prices = market_context.get("historical_prices")
        if not gap_event and prices and len(prices) >= 2:  # noqa: PLR2004
            gap_threshold = Decimal(str(market_context.get("gap_threshold", "0.02")))
            for i in range(1, len(prices)):
                p1 = Decimal(str(prices[i - 1]))
                p2 = Decimal(str(prices[i]))
                if p1 > 0:
                    pct_change = abs(p2 - p1) / p1
                    if pct_change >= gap_threshold:
                        gap_event = True
                        break
        if gap_event:
            return self._build_error_result(
                RiskRegime.SUSPENDED,
                RiskReasonCode.LIFECYCLE_GATES_BREACH,
                "Gap event detected in price history",
                now,
                status=RiskDecisionStatus.REJECT,
            )

        # 2. Reject stale quotes and stale market data snapshots
        dummy_policy = EffectiveRiskPolicy(
            policy_id="temp-read-only-policy",
            resolved_config=self.config,
            policy_hash="temp-hash",
        )
        freshness_res = validate_market_freshness(
            market_snapshot, dummy_policy, now, market_context
        )
        if not freshness_res["valid"]:
            return self._build_error_result(
                RiskRegime.STALE_DATA,
                RiskReasonCode.STALE_EVIDENCE,
                freshness_res["message"],
                now,
            )

        # 3. Classify session regime
        session_state = market_snapshot.session.lower()
        if session_state in {"closed", "suspended"} or market_context.get(
            "is_suspended", False
        ):
            reg = (
                RiskRegime.MARKET_CLOSED
                if session_state == "closed"
                else RiskRegime.SUSPENDED
            )
            return self._build_error_result(
                reg,
                RiskReasonCode.LIFECYCLE_GATES_BREACH,
                f"Trading disabled: market session is '{session_state}' "
                "or symbol is suspended",
                now,
            )
        session_regime = SessionRegime.ACTIVE

        # 4. Classify spread regime (spread-to-sigma thresholds)
        spread_regime = self._classify_spread(market_snapshot.spread, market_context)

        # 5. Classify volatility regime using rolling windows
        volatility_regime = self._classify_volatility(
            market_snapshot.volatility, market_context
        )

        # 6. Classify liquidity regime
        liquidity_regime = self._classify_liquidity(
            market_snapshot.spread, market_context
        )

        # 7. Classify news regime
        news_regime = self._classify_news(calendar_evidence, market_context, now)

        # 8. Classify rollover regime
        rollover_regime = self._classify_rollover(
            market_snapshot.rollover_time, now, market_context, dummy_policy
        )

        # Fail-closed calendar evidence check for live-sensitive profiles
        is_live = getattr(self.config, "allow_live_execution", False)
        require_calendar = market_context.get("require_news_calendar", True)
        if is_live and require_calendar and not calendar_evidence:
            return self._build_error_result(
                RiskRegime.STALE_DATA,
                RiskReasonCode.STALE_EVIDENCE,
                "Live profile execution blocked: news calendar evidence is missing",
                now,
                status=RiskDecisionStatus.BLOCK,
            )

        return self._synthesize_regime(
            spread_regime,
            volatility_regime,
            liquidity_regime,
            news_regime,
            rollover_regime,
            session_regime,
            now,
        )

    def _synthesize_regime(
        self,
        spread_regime: SpreadRegime,
        volatility_regime: VolatilityRegime,
        liquidity_regime: LiquidityRegime,
        news_regime: NewsRegime,
        rollover_regime: RolloverRegime,
        session_regime: SessionRegime,
        now: datetime,
    ) -> RegimeAssessment:
        """Synthesize final regime classification and status logic.

        Args:
            spread_regime: Classified spread regime.
            volatility_regime: Classified volatility regime.
            liquidity_regime: Classified liquidity regime.
            news_regime: Classified news regime.
            rollover_regime: Classified rollover regime.
            session_regime: Classified session regime.
            now: Current UTC timestamp.

        Returns:
            RegimeAssessment: Synthesized regime metrics and status.
        """
        logger.debug("Synthesizing final regime assessment.")
        status = RiskDecisionStatus.APPROVE
        regime = RiskRegime.NORMAL
        reason = "Market regimes are within safe operating limits"
        reason_code = RiskReasonCode.OK

        if rollover_regime == RolloverRegime.BLACKOUT:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.ROLLOVER_BLACKOUT
            reason = "Rollover blackout window is active"
            reason_code = RiskReasonCode.ROLLOVER_BLACKOUT
        elif news_regime == NewsRegime.BLACKOUT:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.NEWS_BLACKOUT
            reason = "High impact news blackout window is active"
            reason_code = RiskReasonCode.NEWS_BLACKOUT
        elif volatility_regime == VolatilityRegime.SPIKE:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.HIGH_VOLATILITY
            reason = "Abnormal volatility spike detected"
            reason_code = RiskReasonCode.DAILY_LOSS_BREACH
        elif spread_regime == SpreadRegime.EXTREME:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.WIDE_SPREAD
            reason = "Extreme spread widening detected"
            reason_code = RiskReasonCode.SPREAD_BREACH
        elif liquidity_regime == LiquidityRegime.ILLIQUID:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.ILLIQUID
            reason = "Illiquid market environment detected"
            reason_code = RiskReasonCode.STALE_EVIDENCE
        elif volatility_regime == VolatilityRegime.HIGH:
            regime = RiskRegime.HIGH_VOLATILITY
            reason = "High volatility regime active"
        elif volatility_regime == VolatilityRegime.LOW:
            regime = RiskRegime.LOW_VOLATILITY
            reason = "Low volatility regime active"
        elif spread_regime == SpreadRegime.WIDE:
            regime = RiskRegime.WIDE_SPREAD
            reason = "Wide spread regime active"

        return RegimeAssessment(
            regime=regime,
            spread_regime=spread_regime,
            volatility_regime=volatility_regime,
            liquidity_regime=liquidity_regime,
            news_regime=news_regime,
            session_regime=session_regime,
            rollover_regime=rollover_regime,
            status=status,
            reason=reason,
            reason_code=reason_code,
            timestamp=now,
        )

    def _classify_spread(
        self, current_spread: Decimal, context: dict[str, Any]
    ) -> SpreadRegime:
        """Classify spread regime based on historical standard deviation.

        Args:
            current_spread: Current spread.
            context: Market context dictionary.

        Returns:
            SpreadRegime: Classified spread regime.
        """
        hist_spreads = context.get("historical_spreads")
        mean_spread = Decimal(0)
        std_spread = Decimal(0)

        if hist_spreads and len(hist_spreads) >= 2:  # noqa: PLR2004
            mean_spread, std_spread = _compute_stats(
                [Decimal(str(x)) for x in hist_spreads]
            )
        else:
            mean_spread_val = context.get("spread_mean")
            std_spread_val = context.get("spread_std")
            if mean_spread_val is not None and std_spread_val is not None:
                mean_spread = Decimal(str(mean_spread_val))
                std_spread = Decimal(str(std_spread_val))

        z_normal = Decimal(str(context.get("spread_z_score_threshold_normal", 1.5)))
        z_wide = Decimal(str(context.get("spread_z_score_threshold_wide", 3.0)))
        thresholds = SpreadSigmaThresholds(
            threshold_normal=z_normal, threshold_wide=z_wide
        )

        return classify_spread_regime(
            current_spread, std_spread, thresholds, mean_spread
        )

    def _fallback_volatility(self, current_vol: Decimal) -> VolatilityRegime:
        """Fallback classification when no history is present.

        Args:
            current_vol: Current volatility metric.

        Returns:
            VolatilityRegime: Classified volatility regime.
        """
        logger.debug("Falling back to volatility classification without history.")
        if current_vol > Decimal("0.05"):
            return VolatilityRegime.HIGH
        if current_vol < Decimal("0.005"):
            return VolatilityRegime.LOW
        return VolatilityRegime.NORMAL

    def _classify_volatility(
        self, current_vol: Decimal, context: dict[str, Any]
    ) -> VolatilityRegime:
        """Classify volatility regime using rolling window relationships.

        Args:
            current_vol: Current volatility metric.
            context: Market context dictionary.

        Returns:
            VolatilityRegime: Classified volatility regime.
        """
        prices = context.get("historical_prices")
        vol_short = Decimal(0)
        vol_med = Decimal(0)
        vol_long = Decimal(0)
        has_history = False

        if prices and len(prices) > 60:  # noqa: PLR2004
            vol_short = _calculate_rolling_vol(prices, 5)
            vol_med = _calculate_rolling_vol(prices, 20)
            vol_long = _calculate_rolling_vol(prices, 60)
            has_history = True
        else:
            v_short = context.get("vol_short")
            v_med = context.get("vol_med")
            v_long = context.get("vol_long")
            if v_short is not None and v_long is not None:
                vol_short = Decimal(str(v_short))
                vol_med = Decimal(str(v_med)) if v_med is not None else vol_short
                vol_long = Decimal(str(v_long))
                has_history = True

        if not has_history:
            return self._fallback_volatility(current_vol)

        ratio_spike = Decimal(str(context.get("volatility_spike_multiplier", 2.0)))
        ratio_high = Decimal(str(context.get("volatility_high_multiplier", 1.3)))
        ratio_low = Decimal(str(context.get("volatility_low_multiplier", 0.5)))
        thresholds = VolatilityThresholds(
            spike_multiplier=ratio_spike,
            high_multiplier=ratio_high,
            low_multiplier=ratio_low,
        )

        return classify_volatility_regime(vol_short, vol_med, vol_long, thresholds)

    def _classify_liquidity(
        self, current_spread: Decimal, context: dict[str, Any]
    ) -> LiquidityRegime:
        """Classify liquidity regime from frequency, missing bars, and gaps.

        Args:
            current_spread: Current spread.
            context: Market context dictionary.

        Returns:
            LiquidityRegime: Classified liquidity regime.
        """
        logger.debug("Classifying liquidity regime.")
        tick_frequency = context.get("tick_frequency")  # Ticks per minute
        missing_bars = context.get("missing_bars", 0)
        stale_seconds = context.get("stale_seconds", 0)

        # Check tick availability explicitly
        tick_availability = context.get("tick_availability", True)
        if not tick_availability:
            return LiquidityRegime.ILLIQUID

        # Check for spread jumps: if current spread is wider than
        # max_spread_multiplier times the mean spread
        spread_jump = context.get("spread_jump", False)
        if not spread_jump:
            mean_spread_val = context.get("spread_mean")
            if mean_spread_val is not None:
                mean_spread = Decimal(str(mean_spread_val))
                config_mult = getattr(self.config, "max_spread_multiplier", 3.0)
                mult = Decimal(str(context.get("max_spread_multiplier", config_mult)))
                if mean_spread > 0 and current_spread > mean_spread * mult:
                    spread_jump = True

        # Check session context
        session_context = str(context.get("session_context", "")).lower()
        # Adjust thresholds if session is thin/Asian
        thin_sessions = {"low_liquidity", "thin", "asian", "off_hours"}
        freq_multiplier = (
            Decimal("0.5") if session_context in thin_sessions else Decimal("1.0")
        )

        # Check for missing bars or quote staleness first
        if missing_bars >= 5 or stale_seconds >= 300 or spread_jump:  # noqa: PLR2004
            return LiquidityRegime.ILLIQUID
        if missing_bars >= 2 or stale_seconds >= 60:  # noqa: PLR2004
            return LiquidityRegime.THIN

        if tick_frequency is not None:
            freq = Decimal(str(tick_frequency))
            illiquid_thresh = Decimal(2) * freq_multiplier
            thin_thresh = Decimal(10) * freq_multiplier
            if freq <= illiquid_thresh:
                return LiquidityRegime.ILLIQUID
            if freq <= thin_thresh:
                return LiquidityRegime.THIN

        return LiquidityRegime.NORMAL

    def _is_event_relevant(self, event: dict[str, Any], currencies: set[str]) -> bool:
        """Check if calendar event matches target currencies or symbol.

        Args:
            event: The calendar event dictionary.
            currencies: Set of currencies to match against.

        Returns:
            bool: True if relevant.
        """
        event_symbol = str(event.get("symbol", "")).upper()
        event_currency = str(event.get("currency", "")).upper()
        if not event_symbol and not event_currency:
            return True
        return event_symbol in currencies or event_currency in currencies

    def _classify_news(
        self,
        calendar_evidence: list[dict[str, Any]],
        context: dict[str, Any],
        now: datetime,
    ) -> NewsRegime:
        """Classify news blackout schedules from upcoming events.

        Args:
            calendar_evidence: Calendar news evidence list.
            context: Market context dictionary.
            now: Current datetime.

        Returns:
            NewsRegime: Classified news regime.
        """
        logger.debug("Classifying news regime.")
        if not calendar_evidence:
            return NewsRegime.NORMAL

        # Default blackout distance: 5 minutes before/after news release
        blackout_mins = float(context.get("news_blackout_mins", 5.0))

        symbol = context.get("symbol", "").upper()
        # Parse currency legs from symbol (e.g. EURUSD -> EUR, USD)
        currencies = {symbol}
        if len(symbol) == 6:  # noqa: PLR2004
            currencies.add(symbol[:3])
            currencies.add(symbol[3:])

        for event in calendar_evidence:
            event_time_raw = event.get("time") or event.get("timestamp")
            if not event_time_raw:
                continue

            event_time = to_utc_datetime(
                parse_datetime(event_time_raw)
                if isinstance(event_time_raw, str)
                else event_time_raw
            )

            if not self._is_event_relevant(event, currencies):
                continue

            delta_seconds = abs((now - event_time).total_seconds())
            if delta_seconds <= blackout_mins * 60:
                impact = str(event.get("impact", "")).upper()
                if impact in {"HIGH", "BLACKOUT"}:
                    return NewsRegime.BLACKOUT
                if impact in {"MEDIUM", "HIGH_IMPACT"}:
                    return NewsRegime.HIGH_IMPACT

        return NewsRegime.NORMAL

    def _classify_rollover(
        self,
        rollover_time: datetime | None,
        now: datetime,
        context: dict[str, Any],
        dummy_policy: EffectiveRiskPolicy,
    ) -> RolloverRegime:
        """Classify rollover blackout window surrounding broker midnight.

        Args:
            rollover_time: Specific next rollover datetime.
            now: Current datetime.
            context: Market context dictionary.
            dummy_policy: Injected EffectiveRiskPolicy reference.

        Returns:
            RolloverRegime: Classified rollover regime.
        """
        logger.debug("Classifying rollover regime.")
        if is_rollover_blackout(now, dummy_policy, context):
            return RolloverRegime.BLACKOUT

        if rollover_time is None:
            return RolloverRegime.NORMAL

        roll_utc = to_utc_datetime(rollover_time)
        before_mins = float(context.get("rollover_blackout_before_mins", 5.0))
        after_mins = float(context.get("rollover_blackout_after_mins", 5.0))

        # Check distance to rollover
        diff_seconds = (now - roll_utc).total_seconds()
        # If now is before rollover_time
        if diff_seconds < 0:
            if abs(diff_seconds) <= before_mins * 60:
                return RolloverRegime.BLACKOUT
        # If now is after rollover_time
        elif diff_seconds <= after_mins * 60:
            return RolloverRegime.BLACKOUT

        return RolloverRegime.NORMAL

    def _build_error_result(
        self,
        regime: RiskRegime,
        reason_code: RiskReasonCode,
        reason: str,
        timestamp: datetime,
        status: RiskDecisionStatus = RiskDecisionStatus.BLOCK,
    ) -> RegimeAssessment:
        """Helper to create fail-closed RegimeAssessment blocks.

        Args:
            regime: Synthesized regime type.
            reason_code: Associated reason code.
            reason: Description of the block/reject.
            timestamp: Timestamp of the assessment.
            status: Decision status outcome. Defaults to BLOCK.

        Returns:
            RegimeAssessment: The error state assessment.
        """
        logger.warning("Market regime assessment blocked: %s", reason)
        return RegimeAssessment(
            regime=regime,
            spread_regime=SpreadRegime.EXTREME,
            volatility_regime=VolatilityRegime.SPIKE,
            liquidity_regime=LiquidityRegime.ILLIQUID,
            news_regime=NewsRegime.BLACKOUT,
            session_regime=SessionRegime.CLOSED,
            rollover_regime=RolloverRegime.BLACKOUT,
            status=status,
            reason=reason,
            reason_code=reason_code,
            timestamp=timestamp,
        )


def assess_risk_regime(  # noqa: C901, PLR0912
    *args: Any,  # noqa: ANN401
    market: MarketRiskSnapshot | None = None,
    policy: EffectiveRiskPolicy | None = None,
    now_utc: datetime | None = None,
    market_snapshot: MarketRiskSnapshot | None = None,
    calendar_evidence: list[dict[str, Any]] | None = None,
    risk_config: RiskConfig | None = None,
    market_context: dict[str, Any] | None = None,
) -> RegimeAssessment:
    """Assess market regime details through public stateless helper.

    Supports both the new position-based clean signature and the old
    keyword-based caller signature.

    Args:
        args: Positional arguments matching V1 or V2 order.
        market: New position-based parameter for MarketRiskSnapshot.
        policy: New position-based parameter for EffectiveRiskPolicy.
        now_utc: New position-based parameter for current UTC datetime.
        market_snapshot: Old keyword-based parameter for MarketRiskSnapshot.
        calendar_evidence: Old keyword-based calendar news list.
        risk_config: Old keyword-based RiskConfig profile.
        market_context: Old keyword-based context parameter dictionary.

    Returns:
        RegimeAssessment: Synthesized regime metrics and decision status.
    """
    logger.info("Entering public assess_risk_regime function wrapper.")

    # 1. Resolve inputs from positional or keyword parameters
    snap = market or market_snapshot
    resolved_config = None
    news = calendar_evidence or []
    ctx = market_context or {}
    time_val = now_utc or utc_now()

    if args:
        snap = args[0]
        if len(args) > 1:
            second_arg = args[1]
            if isinstance(second_arg, EffectiveRiskPolicy):
                resolved_config = second_arg.resolved_config
                if len(args) > 2:  # noqa: PLR2004
                    time_val = args[2]
                if len(args) > 3:  # noqa: PLR2004
                    ctx = args[3]
            else:
                # Old signature: (market_snapshot, calendar_evidence,
                # risk_config, market_context)
                news = second_arg
                if len(args) > 2:  # noqa: PLR2004
                    resolved_config = args[2]
                if len(args) > 3:  # noqa: PLR2004
                    ctx = args[3]

    # Resolve config if not set from positional args
    if resolved_config is None:
        if policy is not None:
            resolved_config = policy.resolved_config
        elif risk_config is not None:
            resolved_config = risk_config
        else:
            raise ValueError("EffectiveRiskPolicy or RiskConfig must be provided.")

    if snap is None:
        raise ValueError("MarketRiskSnapshot must be provided.")

    engine = RegimeRiskEngine(config=resolved_config)
    return engine.assess(
        market_snapshot=snap,
        calendar_evidence=news,
        market_context=ctx,
        now_utc=time_val,
    )
