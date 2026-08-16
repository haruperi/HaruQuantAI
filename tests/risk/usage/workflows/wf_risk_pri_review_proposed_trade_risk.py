"""WF-RISK-PRI: fully illustrated signal-to-Trading Risk pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import get_decision_state, review_trade_risk
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-PRI"
STAGES = (
    "Receive a Strategy signal.",
    "Construct immutable trade-intent lineage.",
    "Construct the Risk-owned proposed trade.",
    "Collect virtual account, position, and pending-order evidence.",
    "Build the immutable portfolio snapshot.",
    "Select and hash the active Risk policy.",
    "Validate identities, environment, lineage, and timestamps.",
    "Assemble the complete kill-switch hierarchy.",
    "Validate evidence freshness.",
    "Assess the supplied market regime.",
    "Evaluate portfolio limits in fixed precedence.",
    "Evaluate market and execution-context limits.",
    "Calculate or disclose the regime-capped requested size.",
    "Project post-trade gross exposure.",
    "Apply concurrent-capacity protection.",
    "Determine authenticated approval requirements.",
    "Invoke the canonical review_trade_risk governor.",
    "Inspect every ordered RiskLimitResult.",
    "Inspect the final RiskDecisionPackage.",
    "Inspect the scoped approval token when approved.",
    "Verify the tamper-evident audit entry.",
    "Illustrate Trading revalidation and token consumption.",
    "Illustrate post-trade evidence refresh with a virtual closed trade.",
    "Illustrate monitoring and non-bypassable kill-switch remediation.",
)


def _stage(number: int, *, actual: bool) -> None:
    """Print one explicitly classified workflow stage.

    Args:
        number: One-based stage number.
        actual: Whether this stage invokes or inspects genuine Risk behavior.
    """
    classification = "ACTUAL RISK EVIDENCE" if actual else "ILLUSTRATIVE BOUNDARY"
    print(
        f"\n{'=' * 88}\nStage {number:02d}/{len(STAGES)} — "
        f"{STAGES[number - 1]}\nClassification: {classification}\n{'=' * 88}"
    )


def _show_mapping(label: str, value: dict[str, object]) -> None:
    """Print a bounded illustrative mapping in stable key order.

    Args:
        label: Human-readable evidence name.
        value: Bounded virtual evidence.
    """
    print(label, {key: value[key] for key in sorted(value)})


def main() -> None:  # noqa: PLR0915 - teaching workflow intentionally linear.
    """Run the complete documented input-to-output Risk workflow."""
    # Stage 01 — INPUT BOUNDARY: Strategy emits (signal) analytical evidence, not authority.
    #   A Strategy identifies a potential trade, for example:
    #   EURUSD, BUY, entry around 1.1000, stop loss 1.0950, take profit 1.1100, strategy: trend-following-v3
    #   A signal is only an analytical result. It has no authority to place an order.

    #   Strategy converts it into an immutable trade intent containing:
    #   - Intent ID
    #   - Strategy ID and version
    #   - Symbol
    #   - OPEN, INCREASE, REDUCE, or CLOSE
    #   - Buy or sell direction
    #   - Proposed entry, stop and target
    #   - Requested size, if Strategy supplies one
    #   - Account and portfolio identity
    #   - Request, workflow and correlation IDs
    #   - Creation and expiration timestamps

    #   Risk retains the complete Strategy intent for lineage.

    _stage(1, actual=False)
    virtual_signal: dict[str, object] = {
        "symbol": "EURUSD",
        "side": "BUY",
        "entry_price": "1.1000",
        "stop_loss": "1.0900",
        "take_profit": "1.1200",
        "strategy": "strategy-1@1.0.0",
    }
    _show_mapping("Virtual Strategy signal:", virtual_signal)
    print("Authority: none — a signal cannot place an order.")

    # Stage 02 — Preserve the exact Strategy contract and immutable lineage.
    _stage(2, actual=True)
    config = examples._config()
    proposal = examples._proposal(config)
    print(
        "Intent lineage:",
        proposal.intent.intent_id,
        proposal.intent.strategy_id,
        proposal.intent.strategy_version,
        proposal.intent.lineage,
    )

    # Stage 03 — Risk receives a non-executable ProposedTrade contract.
    #   Construct the Risk proposal:
    #   The system packages the intent into a Risk-owned ProposedTrade.
    #
    #   The proposal adds facts required to evaluate risk:
    #   - Account ID
    #   - Risk profile
    #   - Current market price
    #   - Market observation time
    #   - Requested size
    #   - Stop-loss distance
    #   - Proposal expiry
    #   - Authenticated request identity
    #   - Strategy intent lineage
    #
    #   Conflicting duplicated facts are rejected. For example, if the Strategy intent says EURUSD
    #   but the market evidence says GBPUSD, Risk fails closed.
    _stage(3, actual=True)
    print(
        "Proposal:",
        proposal.account_id,
        proposal.intent.symbol,
        proposal.requested_size,
        proposal.current_price,
        proposal.expires_at.isoformat(),
    )

    # Stage 04 — Illustrate upstream account state without inventing broker facts.
    #   Collect current evidence:
    #   Risk requires point-in-time evidence rather than reading or inventing values itself.
    #
    #   The input set normally includes:
    #   - Account balance, equity and available margin
    #   - Existing portfolio positions and exposures
    #   - Pending-order exposure
    #   - Daily and cumulative loss
    #   - Current drawdown
    #   - Symbol, currency and correlated exposure
    #   - Effective leverage
    #   - Historical VaR and CVaR evidence
    #   - Current spread and market state
    #   - Volatility and correlation regime evidence
    #   - Applicable firm mandate
    #   - Kill-switch states
    #   - Authenticated principal and permissions
    #   - Current policy configuration
    #
    #   Evidence carries timestamps and provenance references. Missing required evidence does not become zero.
    _stage(4, actual=False)
    virtual_account = {
        "account_id": "account-1",
        "balance": "100000.00",
        "equity": "100000.00",
        "currency": "USD",
    }
    virtual_positions = [
        {
            "ticket": "virtual-open-1",
            "symbol": "GBPUSD",
            "type": "sell",
            "volume": "0.20",
            "status": "illustrative_not_persisted",
        }
    ]
    virtual_pending_orders = [
        {
            "order_id": "virtual-pending-1",
            "symbol": "USDJPY",
            "side": "buy",
            "remaining_volume": "0.10",
        }
    ]
    _show_mapping("Virtual account:", virtual_account)
    print("Virtual positions:", virtual_positions)
    print("Virtual pending orders:", virtual_pending_orders)

    # Stage 05 — Use validated immutable portfolio evidence for the real decision.
    #   Build the portfolio snapshot:
    #   Risk normalizes the supplied account and portfolio facts into an immutable PortfolioRiskSnapshot.
    #
    #   It calculates or records:
    #   - Balance and equity
    #   - Daily and total loss
    #   - Portfolio drawdown
    #   - Gross and net exposure
    #   - Exposure by symbol
    #   - Exposure by currency or another dimension
    #   - Margin utilization
    #   - Free-margin evidence
    #   - Effective leverage
    #   - Portfolio correlation
    #   - Historical VaR and CVaR
    #   - Existing strategy and position exposure
    #   - Evidence timestamps and references
    #
    #   The snapshot is bound to:
    #   - Account
    #   - Request and workflow
    #   - Observation time
    #   - Risk configuration hash
    #   - Source evidence
    _stage(5, actual=True)
    snapshot = examples._snapshot_governor(config)
    print(
        "Snapshot:",
        snapshot.snapshot_id,
        "equity=",
        snapshot.equity,
        "gross_exposure=",
        snapshot.gross_exposure,
    )

    # Stage 06 — Pin the exact policy version and canonical configuration hash.
    #   Select and bind the policy:
    #   The appropriate Risk policy is selected, such as:
    #   - personal-account-default-v1
    #   - prop-firm-default-v1
    #   - A later account-specific policy
    #   - A verified firm-specific mandate
    #
    #   Risk computes the canonical SHA-256 configuration hash. The proposal, snapshot and eventual
    #   decision must all reference the same configuration.
    #
    #   A policy mismatch blocks the request.
    #
    #   The two defaults currently stored are demo-route policies; neither grants live-trading permission.
    _stage(6, actual=True)
    print("Policy:", config.policy_version, config.profile)
    print("Pinned config hash:", snapshot.config_hash)

    # Stage 07 — Display the exact trace and environment bindings validated inside.
    #   Validate the request boundary:
    #   Before evaluating limits, Risk validates:
    #   - Contract and schema versions
    #   - Request, workflow and correlation IDs
    #   - Account identity
    #   - Strategy and intent identity
    #   - Symbol identity
    #   - Risk profile and execution environment
    #   - Proposal expiration
    #   - UTC timestamps and clock skew
    #   - Snapshot configuration hash
    #   - Market observation binding
    #   - Authenticated caller identity and environment
    #   - Firm-mandate verification, when applicable
    #
    #   Any inconsistency fails closed.
    _stage(7, actual=True)
    auth = examples._auth(config)
    print(
        "Bindings:",
        proposal.request_id == auth.request_id,
        proposal.workflow_id == auth.workflow_id,
        proposal.correlation_id == auth.correlation_id,
        proposal.risk_profile == auth.runtime_profile,
    )

    # Stage 08 — Supply every applicable kill-switch scope before limit work.
    #   Check the kill-switch hierarchy:
    #   Kill switches are evaluated before ordinary limits.
    #
    #   The complete applicable hierarchy can include:
    #   1. Global kill switch
    #   2. Portfolio kill switch
    #   3. Strategy kill switch
    #   4. Symbol kill switch
    #
    #   If any applicable state is active, the proposed risk increase is blocked.
    #
    #   For live-sensitive processing, an incomplete or unknown kill-switch hierarchy also blocks.
    #   No caller can override it.
    _stage(8, actual=True)
    inactive_hierarchy = tuple(
        examples._inactive_state(level)
        for level in ("global", "portfolio", "strategy", "symbol")
    )
    print(
        "Kill-switch hierarchy:",
        [(state.scope_level, state.state) for state in inactive_hierarchy],
    )

    # Stage 09 — Freshness is evaluated by the governor; absence never becomes zero.
    #   Validate evidence freshness:
    #   Risk checks each evidence timestamp against the active policy's maximum age.
    #
    #   Examples:
    #   - Portfolio evidence must be no older than its configured limit.
    #   - Market evidence must be no older than its configured limit.
    #   - The decision clock must remain within the permitted clock-skew tolerance.
    #   - Proposal and mandate evidence must still be valid.
    #
    #   Missing, stale or future-dated evidence produces a blocking result rather than a substituted value.
    _stage(9, actual=True)
    market = examples._market()
    print(
        "Evidence times:",
        "portfolio=",
        snapshot.as_of.isoformat(),
        "market=",
        market.as_of.isoformat(),
        "checked=",
        examples.NOW.isoformat(),
    )

    # Stage 10 — Consume a typed deterministic regime assessment.
    #   Assess the market regime:
    #   Risk classifies the supplied market environment using evidence such as:
    #   - Volatility
    #   - Correlation
    #   - Drawdown state
    #   - Crisis-window evidence
    #
    #   The regime might be normal, elevated, high-risk, crisis, or unknown.
    #
    #   A regime modifier may reduce permitted size. For example:
    #   Requested size: 1.00 lot
    #   High-risk modifier: 0.50
    #   Regime-capped size: 0.50 lot
    #
    #   Unknown required regime evidence blocks live-sensitive decisions.
    _stage(10, actual=True)
    regime = examples._regime()
    print("Regime:", regime.assessment_id, dict(regime.states), dict(regime.modifiers))

    # Stage 11 — Portfolio checks execute inside the canonical governor call below.
    #   Evaluate portfolio limits in fixed order:
    #   Risk produces an ordered RiskLimitResult for every applicable check.
    #
    #   The existing portfolio evaluator checks:
    #   1. Portfolio evidence freshness
    #   2. Snapshot consistency
    #   3. Daily loss
    #   4. Total loss
    #   5. Portfolio drawdown
    #   6. Symbol concentration
    #   7. Other configured concentration dimensions
    #   8. Margin utilization
    #   9. Effective leverage
    #   10. Historical VaR
    #   11. Historical CVaR
    #   12. Portfolio correlation
    #
    #   Market-context checks then evaluate applicable conditions such as:
    #   - Spread
    #   - Trading session
    #   - Calendar/news blackout
    #   - Market-context freshness
    #   - Required market evidence
    #
    #   A verified prop-firm mandate can replace generic daily-loss and drawdown limits with the firm's actual rules.
    #
    #   The first failure becomes primary_failure_limit. All failures are retained as ordered composite_breach_flags.
    _stage(11, actual=True)
    print(
        "Portfolio check inputs:",
        "daily_loss=",
        snapshot.daily_loss,
        "drawdown=",
        snapshot.drawdown,
        "margin=",
        snapshot.margin_utilization,
    )

    # Stage 12 — Market checks use the supplied symbol-bound market evidence.
    #   Apply the operational profile limits:
    #   The new policies also contain:
    #   - Maximum and preferred risk per trade
    #   - Daily, weekly and monthly loss limits
    #   - Portfolio, strategy and symbol drawdown limits
    #   - Symbol, currency-cluster and correlated exposure limits
    #   - Total, gross and net exposure limits
    #   - Leverage and margin limits
    #   - Position, order, strategy and trade-count ceilings
    #   - Consecutive-loss limit
    #   - Spread, slippage, commission and swap limits
    #   - Kill-switch loss and drawdown thresholds
    #
    #   Important distinction: a configured limit is evaluated only when trustworthy evidence for it is supplied.
    #   Missing required evidence must block; it must not be treated as passing.
    _stage(12, actual=True)
    print("Market context:", market.symbol, market.spread, market.as_of.isoformat())

    # Stage 13 — The governor applies the strictest supplied regime modifier.
    #   Calculate position size:
    #   Position sizing is deterministic and cannot approve a trade on its own.
    #
    #   Inputs can include:
    #   - Account equity
    #   - Preferred and maximum risk per trade
    #   - Entry price
    #   - Stop-loss price or distance
    #   - Instrument point/tick value
    #   - Contract size
    #   - Minimum and maximum volume
    #   - Volume step
    #   - Existing exposure
    #   - Volatility or correlation adjustment
    #   - Regime modifier
    #   - Margin constraints
    #
    #   Conceptually:
    #   risk capital = equity * permitted risk percentage
    #   raw size = risk capital / loss per unit at stop
    #   approved size = floor raw size to broker volume step
    #
    #   Risk then caps the result using:
    #   - Maximum trade risk
    #   - Symbol and portfolio exposure
    #   - Available margin
    #   - Leverage
    #   - Strategy allocation
    #   - Regime modifier
    #   - Broker volume constraints
    #
    #   If the stop or instrument valuation evidence is absent, Risk cannot safely calculate size.
    _stage(13, actual=True)
    modifier = min(regime.modifiers.values(), default=1)
    illustrative_capped_size = proposal.requested_size * modifier
    print(
        "Requested/regime-capped size:",
        proposal.requested_size,
        illustrative_capped_size,
    )

    # Stage 14 — Mirror the documented projection solely to explain the real check.
    #   Project post-trade exposure:
    #   Risk evaluates the portfolio as it would look after the proposed trade.
    #
    #   The current governor explicitly calculates:
    #   projected gross exposure
    #       = current gross exposure
    #       + abs(regime-capped size * current price)
    #
    #   The proposal must not pass merely because the current portfolio is within limits. The projected portfolio
    #   must remain acceptable too.
    #
    #   Pending orders must be included according to the configured policy or the operation blocks if their exposure cannot be established.
    _stage(14, actual=False)
    projected_gross = snapshot.gross_exposure + abs(
        illustrative_capped_size * proposal.current_price
    )
    print("Illustrative projected gross exposure:", projected_gross)
    print("The governor records the authoritative projected check in Stage 17.")

    # Stage 15 — Capacity is guarded inside Risk for approved risk increases.
    #   Reserve concurrent capacity:
    #   Two individually valid trades might become unsafe if approved simultaneously.
    #
    #   For a risk-increasing action, Risk therefore performs a concurrency or capacity gate:
    #   - Derive an identity from the intent, configuration hash and size.
    #   - Reserve account/strategy/symbol capacity.
    #   - Bind the reservation to an expiry.
    #   - Treat an exact existing reservation as idempotent.
    #   - Block if capacity is unavailable.
    #   - Fail closed if the capacity dependency is unavailable.
    #
    #   Where no external capacity guard is configured, atomic approval-token consumption provides the double-spend protection.
    #
    #   Risk-reducing actions do not need a risk-increase capacity reservation.
    _stage(15, actual=True)
    print("Configured concurrency owner: risk_store atomic token consumption")

    # Stage 16 — Supply authenticated human approval evidence for this increase.
    #   Determine whether human approval is required:
    #   After the safety checks:
    #   - A blocked limit produces BLOCK or REJECT.
    #   - A safe risk-reducing action may proceed according to policy.
    #   - A safe risk-increasing action without the required attestation becomes NEEDS_APPROVAL.
    #   - A valid authenticated attestation allows approval processing to continue.
    #
    #   The attestation must match:
    #   - Decision
    #   - Workflow
    #   - Action
    #   - Scope
    #   - Authenticated principal
    #   - Risk configuration
    #   - Validity period
    _stage(16, actual=True)
    attestation = examples._attestation(config)
    print(
        "Attestation:",
        attestation.attestation_id,
        attestation.principal_id,
        attestation.action,
    )

    # Stage 17 — Execute the one canonical fixed-precedence Risk decision call.
    #   Create the Risk decision:
    #   Risk creates an immutable RiskDecisionPackage containing:
    #   - Decision ID
    #   - Intent ID
    #   - Requested size
    #   - Approved size, if approved
    #   - Final state
    #   - Every ordered check
    #   - Primary failure
    #   - Composite breach flags
    #   - Evidence references
    #   - Configuration hash
    #   - Concurrency disclosure
    #   - Recommendations
    #   - Issue and expiration times
    #   - Request, workflow and correlation IDs
    #   - Optional approval token
    #
    #   Possible states include:
    #   - APPROVE
    #   - NEEDS_APPROVAL
    #   - BLOCK
    #   - REJECT
    #
    #   approved_size is absent unless the decision is approved.
    _stage(17, actual=True)
    governor, _, approved_audit = examples._services(config)
    decision = unwrap_risk_response(
        review_trade_risk(
            governor,
            proposal,
            snapshot,
            market,
            regime,
            inactive_hierarchy,
            auth,
            attestation=attestation,
            now=examples.NOW,
        ),
        operation="risk_governor.review_trade_risk",
    )
    print("Canonical verdict:", decision.state)

    # Stage 18 — Show the actual ordered results and fixed precedence.
    _stage(18, actual=True)
    for check in decision.ordered_checks:
        print(
            f"[{check.precedence:02d}] {check.limit_id}: {check.status}",
            f"reason={check.reason_code}",
        )

    # Stage 19 — Inspect the immutable output contract and provenance.
    _stage(19, actual=True)
    print(
        "Decision package:",
        decision.decision_id,
        decision.state,
        "requested=",
        decision.requested_size,
        "approved=",
        decision.approved_size,
    )
    print("Evidence refs:", dict(decision.evidence_refs))
    print(
        "Primary/composite failures:",
        decision.primary_failure_limit,
        decision.composite_breach_flags,
    )

    # Stage 20 — A token exists only for an approved risk-increasing action.
    #   Issue the scoped approval token:
    #   For an approved risk-increasing action, Risk issues a short-lived approval token.
    #
    #   The token is bound to:
    #   - Decision ID
    #   - Intent and action
    #   - Account and scope
    #   - Approved size
    #   - Workflow identity
    #   - Configuration hash
    #   - Expiration
    #   - Authenticated attestation
    #
    #   The token does not grant general trading authority. It authorizes only the exact approved action.
    _stage(20, actual=True)
    print(
        "Approval token:",
        None if decision.token is None else decision.token.token_id,
        "expires=",
        None if decision.token is None else decision.token.expires_at.isoformat(),
    )

    # Stage 21 — Audit must be appended before the governor returns success.
    #   Write tamper-evident audit evidence:
    #   Before returning the decision, Risk appends an audit record containing:
    #   - Decision and event identity
    #   - Ordered results
    #   - Evidence references
    #   - Configuration hash
    #   - Request and correlation IDs
    #   - Timestamp
    #   - Previous audit-record hash
    #   - Current record hash
    #
    #   If mandatory audit persistence fails, approval fails closed.
    #
    #   The decision is also eligible for durable storage in risk_decision_snapshots, while policy versions,
    #   approval state and kill-switch state use their respective Risk tables.
    _stage(21, actual=True)
    audit_record = approved_audit.records[-1]
    print("Audit entry:", audit_record.event_type, audit_record.config_hash)

    # Stage 22 — OUTPUT BOUNDARY: illustrate, but never execute, Trading handoff.
    #   Return the decision to the caller:
    #   Risk returns the decision to the workflow coordinator.
    #   Risk does not send the order to the broker.
    #
    #   Outcomes:
    #   - BLOCK or REJECT: stop the workflow.
    #   - NEEDS_APPROVAL: obtain a valid human attestation and repeat the controlled approval stage.
    #   - APPROVE: forward the exact decision, approved size and token to Trading.
    #
    #   Trading revalidates the decision:
    #   Before execution, Trading verifies:
    #   - Decision has not expired.
    #   - Intent, account, symbol and action match.
    #   - Approved size has not been increased.
    #   - Configuration hash matches.
    #   - Risk decision and token refer to one another.
    #   - Environment and route match.
    #   - Kill-switch state has not invalidated execution.
    #   - Required market and account evidence remains current.
    #
    #   A changed order must return to Risk. Trading cannot enlarge the size or alter the risk-bearing terms.
    #
    #   Atomically consume the token:
    #   Immediately before the risk-increasing side effect, the approval token is:
    #   1. Validated
    #   2. Reserved
    #   3. Atomically consumed
    #   4. Audited
    #
    #   A consumed token cannot be reused. Concurrent attempts result in only one valid consumer.
    #   Unknown token state or persistence failure blocks execution.
    _stage(22, actual=False)
    trading_handoff = {
        "decision_id": decision.decision_id,
        "intent_id": decision.intent_id,
        "approved_size": str(decision.approved_size),
        "config_hash": decision.config_hash,
        "token_present": decision.token is not None,
        "action": "Trading must revalidate and atomically consume; not executed here",
    }
    _show_mapping("Illustrative Trading handoff:", trading_handoff)

    # Stage 23 — Illustrate later authority evidence without inventing a broker fill.
    #   Trading may submit the order:
    #   Only now may Trading route the approved order to simulation, demo or live execution.
    #
    #   The order remains governed by:
    #   - Exact approved size
    #   - Exact account and symbol
    #   - Approved order action
    #   - Environment boundary
    #   - Idempotency controls
    #
    #   A broker rejection or uncertain execution outcome does not cause Risk or Trading to invent a fill.
    #
    #   After broker authority evidence arrives:
    #   - Trading records authoritative events.
    #   - Reduce exposure
    #   - Close positions
    #   - Pause a strategy
    #   - Require review
    #
    #   Trading owns execution of those actions. Risk owns the decision and non-bypassable block state.
    #
    #   The essential rule is:
    #   > A signal becomes executable only after its identity, evidence, policy, kill-switch state, limits, size,
    #   > concurrency, approval and audit trail all agree. Any uncertainty blocks the risk increase.
    _stage(23, actual=False)
    virtual_closed_trade = {
        "ticket": "awaiting_broker_authority",
        "symbol": proposal.intent.symbol,
        "status": "illustrative_only_not_persisted",
        "next_action": "refresh account evidence and rebuild Risk snapshot",
    }
    _show_mapping("Virtual closed-trade placeholder:", virtual_closed_trade)

    # Stage 24 — Execute a second real decision proving the kill switch cannot bypass.
    _stage(24, actual=True)
    active_global = examples._inactive_state().model_copy(
        update={"state": "active", "reason": "global safety stop"}
    )
    blocked_governor, _, blocked_audit = examples._services(config)
    blocked = unwrap_risk_response(
        review_trade_risk(
            blocked_governor,
            proposal,
            snapshot,
            market,
            regime,
            (active_global, *inactive_hierarchy[1:]),
            auth,
            attestation=attestation,
            now=examples.NOW,
        ),
        operation="risk_governor.review_trade_risk",
    )
    print(
        "Blocked scenario:",
        blocked.state,
        "primary=",
        blocked.primary_failure_limit,
        "approved_size=",
        blocked.approved_size,
        "token=",
        blocked.token,
    )
    print("Blocked audit entry:", blocked_audit.records[-1].event_type)
    print("Non-bypassable:", blocked.state is get_decision_state("BLOCK"))


if __name__ == "__main__":
    main()
