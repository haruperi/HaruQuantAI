"""Manual (discretionary) order eligibility preflight orchestration.

Composes Strategy's registered Discretionary Manual Order identity, real
Data-owned account/market evidence, and Risk's own fixed-precedence
``review_trade_risk`` gate into one callable path for a human-initiated
order. The review a discretionary click receives is the *same* review a
strategy-initiated order receives; the only difference is that a real human
``ApprovalAttestation`` stands in for algorithmic pre-approval, exactly as
``review_trade_risk`` already expects (FR-RISK-059).

This module never invents account state, market evidence, or approval —
every fact it cannot obtain from a real source is surfaced as an explicit
gap (``missing_fields``, an ``unknown`` state, or a raised ``RiskDomainError``)
rather than a fabricated value.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from statistics import StatisticsError, correlation
from typing import Any, cast

from app.services.data import (
    build_market_context_evidence,
    build_market_data_request,
    get_market_data,
)
from app.services.risk.approvals import (
    build_risk_approval_state_store,
    create_approval_token_service,
)
from app.services.risk.audit import (
    build_risk_state_store,
    create_risk_audit_chain,
    get_kill_switch_state,
)
from app.services.risk.capacity import build_risk_capacity_guard
from app.services.risk.contracts.factories import (
    create_action_policy_verdict,
    create_approval_attestation,
    create_portfolio_state,
    create_proposed_trade,
)
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.governor.orchestration import (
    create_risk_governor,
    review_trade_risk,
    run_portfolio_risk_governor,
)
from app.services.risk.persistence import (
    create_equity_history_record,
    read_equity_history_record,
    update_equity_history_record,
)
from app.services.risk.portfolio import build_portfolio_risk_snapshot
from app.services.risk.regimes import assess_risk_regime
from app.services.strategy import (
    create_trade_intent_value,
    discretionary_strategy_version_for,
    get_discretionary_strategy_id,
)
from app.utils import canonical_json, derive_stable_id, get_logger

logger = get_logger(__name__)

_KILL_SWITCH_SCOPE_LEVELS = ("global", "portfolio", "strategy", "symbol")
_RETURN_LOOKBACK_BARS = 30
_RISK_INCREASING_INTENTS = frozenset({"OPEN", "INCREASE"})
_MIN_CORRELATION_SAMPLES = 3


def _kill_switch_states(
    *, portfolio_id: str | None, strategy_id: str, symbol: str
) -> tuple[object, ...]:
    """Fetch only the kill-switch scopes applicable to one exact proposal.

    ``review_trade_risk`` blocks the whole decision if *any* state handed to
    it is active, without its own scope filtering — so only the scopes that
    genuinely apply to this proposal are fetched.

    Returns:
        Ordered applicable, currently-recorded kill-switch states.
    """
    scopes: tuple[tuple[str, Mapping[str, str]], ...] = (
        ("global", {}),
        *(
            ()
            if portfolio_id is None
            else (("portfolio", {"portfolio_id": portfolio_id}),)
        ),
        ("strategy", {"strategy_id": strategy_id}),
        ("symbol", {"symbol": symbol}),
    )
    states: list[object] = []
    for level, scope in scopes:
        state = get_kill_switch_state(level, scope)
        if state is not None:
            states.append(state)
    return tuple(states)


def _track_equity(
    *, account_id: str, equity: Decimal, request_id: str, correlation_id: str
) -> tuple[Decimal, Decimal, Decimal]:
    """Read-and-update one account's tracked equity history.

    First observation seeds inception/peak/day-start at the current equity.
    Later observations raise the peak monotonically and reset day-start once
    per UTC calendar day. Never fabricates a history the account does not
    have yet.

    Returns:
        ``(inception_equity, peak_equity, day_start_equity)``.
    """
    now = datetime.now(UTC)
    today = now.date().isoformat()
    created = create_equity_history_record(
        account_id=account_id,
        inception_equity=str(equity),
        peak_equity=str(equity),
        day_start_equity=str(equity),
        day_start_date=today,
        request_id=request_id,
        correlation_id=correlation_id,
        created_at=now.isoformat(),
    )
    if created:
        return equity, equity, equity
    row = read_equity_history_record(account_id)
    if row is None:
        # Lost a race with a concurrent first-observation insert; re-read once.
        row = read_equity_history_record(account_id)
    if row is None:
        return equity, equity, equity
    inception = Decimal(str(row["inception_equity"]))
    peak = max(Decimal(str(row["peak_equity"])), equity)
    day_start = (
        equity
        if str(row["day_start_date"]) != today
        else Decimal(str(row["day_start_equity"]))
    )
    if peak != Decimal(str(row["peak_equity"])) or day_start != Decimal(
        str(row["day_start_equity"])
    ):
        try:
            update_equity_history_record(
                account_id=account_id,
                peak_equity=str(peak),
                day_start_equity=str(day_start),
                day_start_date=today,
                updated_at=now.isoformat(),
                expected_revision=str(row["updated_at"]),
            )
        except ValueError:
            logger.info("Risk equity history update raced; using the read values")
    return inception, peak, day_start


def _closing_returns(
    source_id: str, symbol: str, *, request_id: str
) -> tuple[Decimal, ...]:
    """Fetch real recent daily bars and compute simple closing returns.

    Never fabricates a return series: an unavailable dataset yields an empty
    tuple rather than synthetic values.

    Returns:
        Ordered simple returns, oldest first; empty if bars are unavailable.
    """
    try:
        response = get_market_data(
            build_market_data_request(
                source_id=source_id,
                symbol=symbol,
                data_kind="bars",
                timeframe="D1",
                limit=_RETURN_LOOKBACK_BARS,
                use_cache=True,
                quality_failure_behavior="warn",
                workflow_context="research",
                precision_policy="decimal_string",
                request_id=request_id,
            )
        )
    except Exception:
        logger.exception("Risk manual preflight could not fetch bars for %s", symbol)
        return ()
    if response.status != "success" or response.data is None:
        return ()
    closes = [record.close for record in response.data.records]
    return tuple(
        (closes[index] - closes[index - 1]) / closes[index - 1]
        for index in range(1, len(closes))
        if closes[index - 1] != 0
    )


def _correlation(left: Sequence[Decimal], right: Sequence[Decimal]) -> Decimal | None:
    """Compute a real Pearson correlation between two equal-length series.

    Returns:
        Correlation in ``[-1, 1]``, or ``None`` when it cannot be computed.
    """
    length = min(len(left), len(right))
    if length < _MIN_CORRELATION_SAMPLES:
        return None
    try:
        value = correlation(
            [float(item) for item in left[-length:]],
            [float(item) for item in right[-length:]],
        )
    except ValueError, ZeroDivisionError, StatisticsError:
        return None
    if value != value:  # noqa: PLR0124 - real NaN guard, not a self-comparison typo
        return None
    return Decimal(str(max(-1.0, min(1.0, value))))


def _market_correlations(
    source_id: str, symbol: str, basket: Sequence[str], *, request_id: str
) -> Mapping[str, Decimal]:
    """Correlate one symbol's real returns against a basket of other symbols.

    The basket is the account's other currently open-position symbols, per
    owner decision. Never invents a correlation for a pair with insufficient
    real return history — that pair is simply omitted.

    Returns:
        Mapping of basket symbol to real computed correlation.
    """
    subject_returns = _closing_returns(source_id, symbol, request_id=request_id)
    correlations: dict[str, Decimal] = {}
    for other in basket:
        if other == symbol:
            continue
        other_returns = _closing_returns(source_id, other, request_id=request_id)
        value = _correlation(subject_returns, other_returns)
        if value is not None:
            correlations[other] = value
    return correlations


def _portfolio_correlations(
    source_id: str, symbols: Sequence[str], *, request_id: str
) -> Mapping[str, Decimal]:
    """Compute real canonical-lexical-pair correlations among held symbols.

    Returns:
        Mapping keyed ``"SYM_A|SYM_B"`` (``SYM_A`` lexically first).
    """
    unique = sorted(set(symbols))
    returns = {
        symbol: _closing_returns(source_id, symbol, request_id=request_id)
        for symbol in unique
    }
    correlations: dict[str, Decimal] = {}
    for index, left in enumerate(unique):
        for right in unique[index + 1 :]:
            value = _correlation(returns[left], returns[right])
            if value is not None:
                correlations[f"{left}|{right}"] = value
    return correlations


def _session_state(
    source_id: str, symbol: str, *, timezone: str, request_id: str
) -> tuple[str, Mapping[str, str]]:
    """Classify session open/closed, preferring a real broker calendar.

    Falls back to real region-active labels (mapped to open/closed) only
    when the broker adapter has no trading-session calendar (true for MT5
    today); never fabricates either value.

    Returns:
        ``(session_state, provenance)``.
    """
    from app.services.data import get_market_hours

    try:
        hours = get_market_hours(
            source_id=source_id, symbol=symbol, timezone=timezone, request_id=request_id
        )
        if hours.status == "success" and hours.data is not None:
            return ("open" if hours.data.is_open else "closed"), {
                "session_source": "broker_calendar"
            }
    except Exception:  # noqa: BLE001 - broker calendar absence must degrade, not crash
        logger.debug("Broker trading-session calendar unavailable for %s", symbol)
    from app.services.data import (
        build_active_market_sessions_request,
        get_active_market_sessions,
    )

    try:
        active = get_active_market_sessions(
            build_active_market_sessions_request(
                symbol=symbol, at=datetime.now(UTC), request_id=request_id
            )
        )
        if active.status == "success" and active.data is not None:
            state = "open" if active.data.sessions else "closed"
            # provenance values must be non-empty; omit the key rather than
            # report an empty joined list when no region is currently active.
            provenance = {"session_source": "regional_named_sessions"}
            if active.data.sessions:
                provenance["active_sessions"] = ",".join(active.data.sessions)
            return state, provenance
    except Exception:  # noqa: BLE001 - regional fallback absence must degrade, not crash
        logger.debug("Regional named-session fallback unavailable for %s", symbol)
    return "unknown", {"session_source": "unavailable"}


def _indicator_value(
    result: object, *, output_columns: Sequence[str]
) -> Decimal | None:
    """Extract the latest real value from one indicator result frame.

    Returns:
        The latest computed Decimal value, or ``None`` if unavailable.
    """
    try:
        frame = result.values  # type: ignore[attr-defined]
        column = output_columns[-1]
        latest = frame[column].iloc[-1]
    except Exception:  # noqa: BLE001 - a malformed indicator frame must degrade, not crash
        return None
    if latest is None or latest != latest:  # noqa: PLR0124 - real NaN guard
        return None
    return Decimal(str(latest))


def _spread(
    source_id: str, symbol: str, *, request_id: str
) -> tuple[Decimal | None, str]:
    """Read a real current spread from a live Level-1 snapshot.

    Returns:
        ``(spread, spread_unit)``; ``spread`` is ``None`` when unavailable.
    """
    from app.services.data import get_level1_snapshot

    try:
        snapshot = get_level1_snapshot(
            source_id=source_id, symbol=symbol, request_id=request_id
        )
        if snapshot.status == "success" and snapshot.data is not None:
            return snapshot.data.spread, snapshot.data.price_unit or "quote_currency"
    except Exception:  # noqa: BLE001 - an unavailable quote must degrade, not crash
        logger.debug("Level-1 snapshot unavailable for %s", symbol)
    return None, "quote_currency"


def _calendar_state(symbol: str, *, now: datetime) -> tuple[str, Mapping[str, str]]:
    """Derive real calendar state from persisted, genuinely scraped events.

    ``populate_market_context_calendar`` requires an injected
    ``EconomicEventStore`` (Data's real scraped-event persistence) that has
    no public composition-root factory yet — wiring one is a real, tracked
    follow-up, not something to fabricate a placeholder for here. Until that
    store is composed, calendar state is honestly ``"unknown"`` rather than
    invented.

    Returns:
        ``(calendar_state, provenance)``; always ``"unknown"`` today.
    """
    del symbol, now
    return "unknown", {}


def _volatility_and_liquidity(
    source_id: str, symbol: str, *, request_id: str
) -> tuple[Decimal | None, Decimal | None]:
    """Compute real volatility (ATR) and liquidity (Amihud) from real bars.

    Returns:
        ``(volatility, liquidity)``; either is ``None`` when unavailable.
    """
    try:
        from app.services.indicators import amihud_illiquidity, atr

        bars = get_market_data(
            build_market_data_request(
                source_id=source_id,
                symbol=symbol,
                data_kind="bars",
                timeframe="D1",
                limit=_RETURN_LOOKBACK_BARS,
                use_cache=True,
                quality_failure_behavior="warn",
                workflow_context="research",
                precision_policy="decimal_string",
                request_id=request_id,
            )
        )
        if bars.status == "success" and bars.data is not None:
            atr_result = atr(bars.data, period=14)
            liquidity_result = amihud_illiquidity(bars.data, window=14)
            return (
                _indicator_value(atr_result, output_columns=atr_result.output_columns),
                _indicator_value(
                    liquidity_result, output_columns=liquidity_result.output_columns
                ),
            )
    except Exception:  # noqa: BLE001 - unavailable indicator inputs must degrade, not crash
        logger.debug("Volatility/liquidity computation unavailable for %s", symbol)
    return None, None


def _build_market_context(
    *,
    source_id: str,
    symbol: str,
    basket: Sequence[str],
    timezone: str,
    request_id: str,
    now: datetime,
) -> object:
    """Assemble real Data-owned market-context evidence for one symbol.

    Every field is sourced from a real read where a source exists in this
    codebase today (spread, volatility, liquidity, session state where the
    broker supports it, calendar state where events are available,
    correlation against the account's other held symbols). Any field with no
    real source is left explicitly absent and listed in ``missing_fields``
    rather than invented.

    Returns:
        Validated ``MarketContextEvidence``.
    """
    missing: list[str] = []

    spread, spread_unit = _spread(source_id, symbol, request_id=request_id)
    if spread is None:
        missing.append("spread")

    session_state, session_provenance = _session_state(
        source_id, symbol, timezone=timezone, request_id=request_id
    )
    if session_state == "unknown":
        missing.append("session_state")

    calendar_state, calendar_provenance = _calendar_state(symbol, now=now)
    if calendar_state == "unknown":
        missing.append("calendar_state")

    volatility, liquidity = _volatility_and_liquidity(
        source_id, symbol, request_id=request_id
    )
    if volatility is None:
        missing.append("volatility")
    if liquidity is None:
        missing.append("liquidity")

    correlations = _market_correlations(
        source_id, symbol, basket, request_id=request_id
    )

    provenance = {"source": source_id, **session_provenance, **calendar_provenance}

    return build_market_context_evidence(
        symbol=symbol,
        session_state=session_state,
        calendar_state=calendar_state,
        spread=spread if spread is not None else Decimal(0),
        spread_unit=spread_unit,
        liquidity=liquidity if liquidity is not None else Decimal(0),
        volatility=volatility if volatility is not None else Decimal(0),
        correlations=correlations,
        crisis_flags=(),
        timezone=timezone,
        as_of=now,
        expires_at=now + timedelta(minutes=1),
        provenance=provenance,
        missing_fields=tuple(missing),
        request_id=request_id,
    )


def _authorization_verifier(auth: object) -> Callable[[object], bool]:
    """Build a request-scoped attestation-authorization check.

    Valid only when the attesting principal is the same principal already
    authenticated for this request, and that principal's session already
    carries the permission the attested action requires. Reuses the
    existing permission model; introduces no new policy engine.

    Returns:
        A closure suitable as ``ApprovalTokenService``'s authorization_verifier.
    """

    def _verify(attestation: object) -> bool:
        candidate = cast("Any", attestation)
        principal_id = getattr(auth, "principal_id", None)
        permissions = getattr(auth, "permissions", ())
        required = (
            "trading:write"
            if candidate.action in {"submit_order", "cancel_order", "cancel_all_orders"}
            else "trading:read"
        )
        return candidate.principal_id == principal_id and required in permissions

    return _verify


def review_manual_order(
    *,
    account_snapshot: object,
    proposal_symbol: str,
    proposal_side: str,
    proposal_order_type: str,
    proposal_quantity: Decimal,
    proposal_current_price: Decimal,
    proposal_stop_distance: Decimal | None,
    portfolio_id: str | None,
    route: str,
    risk_config: object,
    secret_resolver: Callable[[str], bytes],
    auth: object,
    request_id: str,
    workflow_id: str,
    correlation_id: str,
    now: datetime | None = None,
    market_evidence_time: datetime | None = None,
    temporal_context: str = "runtime",
    historical_evidence_refs: Mapping[str, str] | None = None,
) -> object:
    """Review one human-initiated order through Risk's real fixed-precedence gate.

    Composes a Strategy-owned ``TradeIntent`` for the registered Discretionary
    Manual Order strategy, real Data-owned account/market evidence, real
    kill-switch state for the applicable scopes, and a real human
    ``ApprovalAttestation`` (bound to the current authenticated caller) into
    exactly the same ``review_trade_risk`` call an agentic order receives.

    Args:
        account_snapshot: A real ``AccountStateSnapshot`` produced by
            ``app.services.data.get_account_state_snapshot`` against a live,
            already-connected broker adapter. Obtaining that connection is a
            composition-root concern outside Risk's domain boundary.
        proposal_symbol: Broker-native instrument symbol.
        proposal_side: ``"BUY"`` or ``"SELL"``.
        proposal_order_type: ``"MARKET"``, ``"LIMIT"``, ``"STOP"``, or
            ``"STOP_LIMIT"``.
        proposal_quantity: Requested order size.
        proposal_current_price: Current price used for exposure projection.
        proposal_stop_distance: Optional stop distance for the readiness gate.
        portfolio_id: Optional bound portfolio scope.
        route: ``"demo"`` or ``"live"``, matching Trading's own route domain.
        risk_config: A real, already-constructed ``RiskConfig`` for this route.
        secret_resolver: Resolves the approval-token signing key; supplied by
            the API composition root, which owns encrypted-credential access.
        auth: The current request's authenticated context.
        request_id: Canonical request identity, shared across every evidence
            object this call assembles.
        workflow_id: Canonical workflow identity.
        correlation_id: Canonical correlation identity.
        now: Explicit decision time; defaults to the real current UTC time.
        market_evidence_time: Historical market time for Simulation evidence.
        temporal_context: ``runtime`` or ``historical_simulation``.
        historical_evidence_refs: Exact session, dataset revision, and cursor
            bindings required for historical Simulation review.

    Returns:
        The ``RiskDecisionPackage`` produced by ``review_trade_risk``, plus
        the ``ActionPolicyVerdict`` reserved capacity produced, as a
        ``(decision, verdict)`` tuple. ``verdict`` is ``None`` when the
        decision did not reach ``APPROVE``.

    Raises:
        RiskDomainError: If validation, evidence, approval, or persistence
            fails anywhere in the fixed-precedence review.
        ValueError: If historical temporal evidence is incomplete or is used
            outside the Simulation route.
    """
    checked_now = now or datetime.now(UTC)
    evidence_now = market_evidence_time or checked_now
    if temporal_context not in {"runtime", "historical_simulation"}:
        raise ValueError("temporal_context is invalid")
    if temporal_context == "historical_simulation":
        if route != "sim" or market_evidence_time is None:
            raise ValueError("historical simulation requires sim evidence time")
        required_refs = {"simulation_session_id", "dataset_revision", "replay_cursor"}
        if historical_evidence_refs is None or not required_refs <= set(
            historical_evidence_refs
        ):
            raise ValueError("historical simulation evidence identity is incomplete")
    environment = "LIVE" if route == "live" else "SIM" if route == "sim" else "DEMO"
    strategy_id = get_discretionary_strategy_id()
    strategy_version = discretionary_strategy_version_for(environment)
    # account_snapshot/risk_config/auth are intentionally opaque at this
    # function's own boundary (Function-Only Public API Surface); their real
    # shapes are Data's AccountStateSnapshot, Risk's RiskConfig, and the
    # shared AuthContext, produced by this call's own caller.
    account = cast("Any", account_snapshot)
    config = cast("Any", risk_config)

    # generate_id only mints from a small closed trace-prefix vocabulary that
    # has no "intent"/"decision"/"idem" entry, and a retried identical request
    # should yield the same sub-identities anyway — so these are deterministic
    # derivations of the real request_id rather than fresh random trace ids.
    intent = create_trade_intent_value(
        intent_id=derive_stable_id("id", f"manual-preflight-intent:{request_id}"),
        decision_id=derive_stable_id("id", f"manual-preflight-decision:{request_id}"),
        idempotency_key=derive_stable_id("id", f"manual-preflight-idem:{request_id}"),
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        strategy_sequence=0,
        symbol=proposal_symbol,
        side=proposal_side,
        intent_type="OPEN",
        order_type=proposal_order_type,
        limit_price=proposal_current_price if proposal_order_type == "LIMIT" else None,
        stop_price=None,
        time_in_force=None,
        requested_sizing_mode=None,
        quantity_hint=proposal_quantity,
        notional_hint=None,
        signal_timestamp=evidence_now,
        decision_timestamp=checked_now,
        parent_intent_id=None,
        stop_loss=None,
        take_profit=None,
        expiration=None,
        allow_partial_fills=False,
        min_fill_size=None,
        rationale_ref=None,
        lineage={
            "origin": "manual_preflight",
            "principal_id": str(getattr(auth, "principal_id", "")),
        },
    )

    open_symbols = tuple({str(position.symbol) for position in account.positions})
    inception_equity, peak_equity, day_start_equity = _track_equity(
        account_id=account.account_id,
        equity=account.equity,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    portfolio_state = create_portfolio_state(
        account_snapshot=account,
        peak_equity=peak_equity,
        day_start_equity=day_start_equity,
        inception_equity=inception_equity,
        symbol_prices={proposal_symbol: proposal_current_price},
        symbol_contract_sizes={},
        symbol_quote_currencies={},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations=_portfolio_correlations(
            "simulator" if route == "sim" else "mt5",
            (*open_symbols, proposal_symbol),
            request_id=request_id,
        ),
        exposure_dimensions={},
        as_of=evidence_now,
        expires_at=evidence_now + timedelta(minutes=1),
        provenance={
            "source": "manual_preflight",
            "temporal_context": temporal_context,
            **dict(historical_evidence_refs or {}),
        },
        missing_fields=(),
        request_id=request_id,
        workflow_id=workflow_id,
    )
    snapshot = unwrap_risk_response(
        build_portfolio_risk_snapshot(portfolio_state, config, now=evidence_now),
        operation="build_portfolio_risk_snapshot",
    )

    market_evidence = cast(
        "Any",
        _build_market_context(
            source_id="simulator" if route == "sim" else "mt5",
            symbol=proposal_symbol,
            basket=open_symbols,
            timezone="UTC",
            request_id=request_id,
            now=evidence_now,
        ),
    )
    regime = unwrap_risk_response(
        assess_risk_regime(snapshot, market_evidence, config, now=evidence_now),
        operation="assess_risk_regime",
    )

    kill_switch_states = cast(
        "Any",
        _kill_switch_states(
            portfolio_id=portfolio_id, strategy_id=strategy_id, symbol=proposal_symbol
        ),
    )

    proposal = create_proposed_trade(
        intent=intent,
        account_id=account.account_id,
        portfolio_id=portfolio_id,
        requested_size=proposal_quantity,
        current_price=proposal_current_price,
        stop_distance=proposal_stop_distance,
        market_as_of=evidence_now,
        expires_at=checked_now + timedelta(minutes=5),
        risk_profile="simulation" if route == "sim" else route,
        evidence_refs={
            "account": account.account_id,
            "market": proposal_symbol,
            **dict(historical_evidence_refs or {}),
        },
        provenance={
            "source": "manual_preflight",
            "temporal_context": temporal_context,
        },
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
    )

    # A zero-tolerance `clock_skew_tolerance_seconds` policy requires the
    # governor's own injected clock to agree with the `now` handed to
    # `review_trade_risk` exactly, which a live-resampling clock can never
    # guarantee against a second, independent `datetime.now(UTC)` call. One
    # instant is captured here and frozen into the clock closure for this
    # single review's audit/approval/governor bookkeeping instead.
    governor_now = checked_now
    clock = lambda: governor_now  # noqa: E731 - frozen shared clock, not a named def
    audit = create_risk_audit_chain(
        config, cast("Any", build_risk_state_store()), clock, canonical_json
    )
    approvals = create_approval_token_service(
        config,
        cast("Any", build_risk_approval_state_store()),
        audit,
        clock,
        secret_resolver,
        _authorization_verifier(auth),
    )
    governor = create_risk_governor(
        config, approvals, audit, clock, cast("Any", build_risk_capacity_guard())
    )

    attestation = cast(
        "Any",
        create_approval_attestation(
            attestation_id=derive_stable_id(
                "id", f"manual-preflight-attest:{request_id}"
            ),
            principal_id=str(getattr(auth, "principal_id", "")),
            action="submit_order",
            scope={"account_id": account.account_id, "symbol": proposal_symbol},
            policy_ref="manual-order-confirmation",
            policy_version="v1",
            issued_at=checked_now,
            expires_at=checked_now + timedelta(minutes=5),
            request_id=request_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
        ),
    )

    decision = cast(
        "Any",
        unwrap_risk_response(
            cast(
                "Any",
                review_trade_risk(
                    governor,
                    proposal,
                    snapshot,
                    market_evidence,
                    regime,
                    kill_switch_states,
                    auth,
                    attestation=attestation,
                    now=governor_now,
                    evidence_now=evidence_now,
                ),
            ),
            operation="review_trade_risk",
        ),
    )

    if decision.state.value != "approve" or decision.token is None:
        return decision, None

    verdict = create_action_policy_verdict(
        verdict_id=derive_stable_id("id", f"manual-preflight-verdict:{request_id}"),
        action="submit_order",
        scope={"account_id": account.account_id, "symbol": proposal_symbol},
        policy_version="v1",
        attestation_id=attestation.attestation_id,
        decision_id=decision.decision_id,
        reservation_id=decision.decision_id,
        allowed=True,
        reasons=(),
        issued_at=checked_now,
        expires_at=decision.expires_at,
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
    )
    return decision, verdict


def review_cancel_authorization(
    *,
    account_snapshot: object,
    representative_symbol: str,
    action: str,
    action_scope: Mapping[str, str],
    portfolio_id: str | None,
    risk_config: object,
    secret_resolver: Callable[[str], bytes],
    auth: object,
    request_id: str,
    workflow_id: str,
    correlation_id: str,
    now: datetime | None = None,
) -> object:
    """Authorize one order cancellation through Risk's real current-state review.

    Covers both a single order (``action="cancel_order"``) and every working
    order (``action="cancel_all_orders"``) through the same real gate: a
    cancellation is inherently risk-reducing (never opens or increases a
    position), so it is reviewed through ``run_portfolio_risk_governor`` —
    Risk's current-state compliance gate — rather than the single-proposal
    ``review_trade_risk`` gate, which structurally assumes one symbol and one
    requested size. A real human ``ApprovalAttestation`` still gates token
    issuance, satisfying the same explicit-confirmation requirement a
    risk-increasing order receives. Neither cancel action's real governance
    reference is retrievable from anywhere else: a working order's own
    original submit-scoped token is not preserved once consumed, and no
    prior review ever authorizes "cancel everything."

    Args:
        account_snapshot: A real ``AccountStateSnapshot`` produced by
            ``app.services.data.get_account_state_snapshot`` against a live,
            already-connected broker adapter.
        representative_symbol: One real symbol — the target order's own
            symbol for ``cancel_order``, or any one of the account's
            currently working orders for ``cancel_all_orders`` — used for the
            market-context slice of the portfolio-level review
            (spread/session/volatility are symbol-scoped; exposure/drawdown
            are not).
        action: ``"cancel_order"`` or ``"cancel_all_orders"``, matching
            Trading's own action identity.
        action_scope: Extra caller-specific ``ActionPolicyVerdict``/attestation
            scope keys beyond ``account_id`` — ``{"target_broker_order_id": ...}``
            for ``cancel_order``. Empty for ``cancel_all_orders``: its
            ``max_children`` ceiling is derived here from the account's own
            registered ``RiskConfig``, not supplied by the caller.
        portfolio_id: Optional bound portfolio scope.
        risk_config: A real, already-constructed ``RiskConfig`` for this route.
        secret_resolver: Resolves the approval-token signing key; supplied by
            the API composition root, which owns encrypted-credential access.
        auth: The current request's authenticated context.
        request_id: Canonical request identity, shared across every evidence
            object this call assembles.
        workflow_id: Canonical workflow identity.
        correlation_id: Canonical correlation identity.
        now: Explicit decision time; defaults to the real current UTC time.

    Returns:
        The ``RiskDecisionPackage`` produced by ``run_portfolio_risk_governor``
        (with its issued token attached when approved), plus the
        ``ActionPolicyVerdict`` scoped ``{"account_id", **action_scope}`` for
        Trading's own cancellation gate, as a ``(decision, verdict)`` tuple.
        ``verdict`` is ``None`` when the decision did not reach ``APPROVE``.

    Raises:
        RiskDomainError: If validation, evidence, approval, or persistence
            fails anywhere in the review.
    """
    checked_now = now or datetime.now(UTC)
    account = cast("Any", account_snapshot)
    config = cast("Any", risk_config)

    open_symbols = tuple({str(position.symbol) for position in account.positions})
    inception_equity, peak_equity, day_start_equity = _track_equity(
        account_id=account.account_id,
        equity=account.equity,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    portfolio_state = create_portfolio_state(
        account_snapshot=account,
        peak_equity=peak_equity,
        day_start_equity=day_start_equity,
        inception_equity=inception_equity,
        symbol_prices={},
        symbol_contract_sizes={},
        symbol_quote_currencies={},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations=_portfolio_correlations(
            "mt5", open_symbols, request_id=request_id
        ),
        exposure_dimensions={},
        as_of=checked_now,
        expires_at=checked_now + timedelta(minutes=1),
        provenance={"source": "cancel_preflight"},
        missing_fields=(),
        request_id=request_id,
        workflow_id=workflow_id,
    )
    snapshot = unwrap_risk_response(
        build_portfolio_risk_snapshot(portfolio_state, config, now=checked_now),
        operation="build_portfolio_risk_snapshot",
    )

    market_evidence = cast(
        "Any",
        _build_market_context(
            source_id="mt5",
            symbol=representative_symbol,
            basket=open_symbols,
            timezone="UTC",
            request_id=request_id,
            now=checked_now,
        ),
    )
    regime = unwrap_risk_response(
        assess_risk_regime(snapshot, market_evidence, config, now=checked_now),
        operation="assess_risk_regime",
    )

    kill_switch_states = cast(
        "Any",
        _kill_switch_states(
            portfolio_id=portfolio_id,
            strategy_id=get_discretionary_strategy_id(),
            symbol=representative_symbol,
        ),
    )

    # See review_manual_order's identical comment: the governor's zero-skew
    # clock check requires this frozen instant, not a live-resampling clock.
    governor_now = checked_now if now is not None else datetime.now(UTC)
    clock = lambda: governor_now  # noqa: E731 - frozen shared clock, not a named def
    audit = create_risk_audit_chain(
        config, cast("Any", build_risk_state_store()), clock, canonical_json
    )
    approvals = create_approval_token_service(
        config,
        cast("Any", build_risk_approval_state_store()),
        audit,
        clock,
        secret_resolver,
        _authorization_verifier(auth),
    )
    governor = create_risk_governor(
        config, approvals, audit, clock, cast("Any", build_risk_capacity_guard())
    )

    # The bulk ceiling is Risk's own to derive (from the account's registered
    # max_pending_orders limit), not a value the caller supplies — callers
    # only ever specify the parts of scope unique to their own request, such
    # as the target order id for a single cancellation.
    derived_scope = (
        {"max_children": str(config.max_pending_orders)}
        if action == "cancel_all_orders"
        else {}
    )
    attestation_scope = {
        "account_id": account.account_id,
        **derived_scope,
        **action_scope,
    }
    attestation = cast(
        "Any",
        create_approval_attestation(
            attestation_id=derive_stable_id(
                "id", f"cancel-preflight-attest:{request_id}"
            ),
            principal_id=str(getattr(auth, "principal_id", "")),
            action=action,
            scope=attestation_scope,
            policy_ref="cancel-confirmation",
            policy_version="v1",
            issued_at=checked_now,
            expires_at=checked_now + timedelta(minutes=5),
            request_id=request_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
        ),
    )

    decision = cast(
        "Any",
        unwrap_risk_response(
            cast(
                "Any",
                run_portfolio_risk_governor(
                    governor,
                    snapshot,
                    market_evidence,
                    regime,
                    kill_switch_states,
                    auth,
                    now=governor_now,
                ),
            ),
            operation="run_portfolio_risk_governor",
        ),
    )

    if decision.state.value != "approve":
        return decision, None

    token = approvals.issue(decision, attestation, now=governor_now)
    decision = decision.model_copy(update={"token": token})

    verdict = create_action_policy_verdict(
        verdict_id=derive_stable_id("id", f"cancel-preflight-verdict:{request_id}"),
        action=action,
        scope=attestation_scope,
        policy_version="v1",
        attestation_id=attestation.attestation_id,
        decision_id=decision.decision_id,
        reservation_id=decision.decision_id,
        allowed=True,
        reasons=(),
        issued_at=checked_now,
        expires_at=decision.expires_at,
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
    )
    return decision, verdict


__all__ = ["review_cancel_authorization", "review_manual_order"]
