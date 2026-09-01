"""Executable FEAT-AGT-20 Trade Proposal Handoff usage example.

Demonstrates every registered public operation through the documented API. The
receiver intake is a deterministic double, so no signal is evaluated, no intent
is constructed, no network call occurs, and Agentic holds no credential.

The point of the demonstration is that a proposal cannot become an order. It
defines no field a broker could act on, its execution vocabulary is refused,
the receiver derives the request identity rather than accepting one, and the
most a receipt can say is that the proposal was accepted for evaluation.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.agentic import build_agent_task, build_model_profile, get_role_registry
from app.agentic.agents.strategy_desk.trader import (
    TradeProposal,
    TradeProposalReceipt,
    build_trade_proposal_receipt,
    submit_trade_proposal,
)
from app.agentic.agents.strategy_desk.trader.agent import (
    PROPOSABLE_STANCES,
    get_proposal_context,
    propose_trade,
)
from app.agentic.agents.strategy_desk.trader.handoff import (
    RECEIVER_DERIVED_FIELDS,
    build_evaluation_request,
)
from app.agentic.agents.strategy_desk.trader.schemas import (
    FORBIDDEN_BROKER_FIELDS,
    MAX_HORIZON_SECONDS,
    forbidden_fields,
)
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id
from app.services.strategy import create_strategy_proposal_evaluation_request

from tests.agentic.usage._runner import run_feature_usage

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.agentic.fixtures import (
    PROPOSAL_EVIDENCE_REFS,
    PROPOSAL_INSTRUMENT,
    PROPOSAL_STRATEGY_ID,
    PROPOSAL_STRATEGY_VERSION,
    build_proposable_thesis,
    build_trader_mandate,
    build_trader_role_manifest,
    receiver_result,
    trader_model_output,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-trade-proposal-usage")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
HORIZON = 4 * 60 * 60
PRINCIPAL = "operator-owner"

BANNER = "=" * 88


def heading(requirement: str, statement: str) -> None:
    """Print one requirement heading.

    Args:
        requirement: Functional requirement identifier.
        statement: What the requirement obliges.
    """
    print(f"\n{BANNER}\n{requirement}: {statement}\n{BANNER}")


class DeterministicRuntime:
    """Deterministic runtime returning declared structured output."""

    def __init__(self, output=None) -> None:
        """Store the output this runtime will return.

        Args:
            output: Optional structured output override.
        """
        self.output = output or trader_model_output()
        self.nodes: list[str] = []

    def execute_node(self, node_id, profile, invocation):
        """Return the declared output for one node.

        Args:
            node_id: Node identity being executed.
            profile: Pinned evaluated model profile.
            invocation: Governed model invocation.

        Returns:
            The deterministic model outcome.
        """
        self.nodes.append(node_id)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": "ok",
                "output": self.output,
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 820,
                "latency_ms": 105,
                "cost": Decimal("0.04"),
            },
        )


class DeterministicIntake:
    """Deterministic stand-in for the receiver-owned proposal intake."""

    def __init__(self, result=None) -> None:
        """Store the result this intake will return.

        Args:
            result: Optional receiver-result override.
        """
        self.result = receiver_result() if result is None else result
        self.requests: list[object] = []

    def submit(self, request):
        """Record the submitted request and return the receiver's result.

        Args:
            request: Receiver-owned proposal-evaluation request.

        Returns:
            The receiver's result fields.
        """
        self.requests.append(request)
        return {
            "source_proposal_id": request.source_proposal_id,
            "source_content_hash": request.source_content_hash,
            **self.result,
        }


class MismatchedIntake(DeterministicIntake):
    """An intake whose result was produced for different proposal content."""

    def submit(self, request):
        """Return a result bound to a digest this proposal does not carry.

        Args:
            request: Receiver-owned proposal-evaluation request.

        Returns:
            A result whose content digest does not match the request.
        """
        self.requests.append(request)
        return {
            "source_proposal_id": request.source_proposal_id,
            "source_content_hash": "b" * 64,
            **self.result,
        }


def profile():
    """Build the pinned evaluated model profile.

    Returns:
        A validated immutable model profile.
    """
    return build_model_profile(
        {
            "profile_id": "profile-market-analysis-a",
            "version": "1.0.0",
            "provider": "gemini",
            "model_identifier": "gemini-3.0-pro-002",
            "region": "europe-west4",
            "credential_ref": "vault://agentic/gemini",
            "structured_output_mode": "json_schema",
            "max_context_tokens": 120_000,
            "max_output_tokens": 8_000,
            "max_latency_ms": 30_000,
            "max_cost_per_call": Decimal("0.50"),
            "retention_policy": "zero-retention",
            "training_use_permitted": False,
            "fallback_profile_id": None,
            "evaluation_state": "evaluated",
            "enabled": True,
        },
    )


def task():
    """Build the bounded governed task.

    Returns:
        A validated immutable agent task.
    """
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "submit_trade_proposal",
            "workflow_version": "1.0.0",
            "objective": "Turn the overlap thesis into an evaluable proposal.",
            "input_refs": PROPOSAL_EVIDENCE_REFS,
            "principal_id": PRINCIPAL,
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-trade-proposal-usage",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def registry():
    """Build the validated role registry.

    Returns:
        A validated Agentic role registry.
    """
    return get_role_registry(
        build_trader_mandate(),
        (build_trader_role_manifest(),),
        NOW,
    )


def propose(**overrides: object):
    """Compose one proposal with optional overrides.

    Args:
        **overrides: Optional argument overrides.

    Returns:
        The typed proposal result.
    """
    data: dict[str, object] = {
        "registry": registry(),
        "task": task(),
        "runtime": DeterministicRuntime(),
        "profile": profile(),
        "thesis": build_proposable_thesis(),
        "strategy_id": PROPOSAL_STRATEGY_ID,
        "strategy_version": PROPOSAL_STRATEGY_VERSION,
        "instrument": PROPOSAL_INSTRUMENT,
        "direction": "BUY",
        "horizon_seconds": HORIZON,
        "evaluation_scope": "SIGNAL_ONLY",
        "at_time": NOW,
    }
    data.update(overrides)
    return propose_trade(**data)


def fr_agentic_058() -> None:
    """Demonstrate the required content and the absent broker vocabulary."""
    heading(
        "FR-AGENTIC-058",
        "A trade proposal carries thesis, instrument, direction, horizon, "
        "invalidation, evidence, uncertainty, evaluation request, and expiry, "
        "with no broker-native fields.",
    )

    proposal = propose().payload
    print(f"  thesis:            {proposal.thesis_id}")
    print(f"  instrument:        {proposal.instrument}")
    print(f"  direction:         {proposal.direction}")
    print(f"  horizon:           {proposal.horizon_seconds}s")
    print(f"  evaluation scope:  {proposal.evaluation_scope}")
    print(f"  evidence:          {len(proposal.evidence_refs)} references")
    print(f"  invalidation:      {len(proposal.invalidation)} conditions")
    print(f"  issued / expires:  {proposal.issued_at} / {proposal.expires_at}")
    print(f"  content digest:    {proposal.content_hash}")

    print("\n  Nothing a broker could act on exists on either contract:")
    print(f"    proposal: {forbidden_fields(TradeProposal) or 'no broker fields'}")
    print(
        f"    receipt:  {forbidden_fields(TradeProposalReceipt) or 'no broker fields'}"
    )
    print(f"    the prohibition list holds {len(FORBIDDEN_BROKER_FIELDS)} names")

    print("\n  Execution vocabulary in prose is refused:")
    for phrase in ("approved", "entry price", "stop loss", "market order", "lot size"):
        outcome = propose(
            runtime=DeterministicRuntime(
                trader_model_output(
                    rationale=f"The thesis supports a {phrase} on the overlap.",
                ),
            ),
        )
        print(f"    {phrase:<14} -> {outcome.reasons[0]}")

    print("\n  The model describes what is proposed; it cannot choose it:")
    hijacked = propose(
        runtime=DeterministicRuntime(
            trader_model_output(
                instrument="GBPUSD",
                direction="SELL",
                evidence_refs="agentic.invented_evidence:nowhere",
            ),
        ),
    ).payload
    print(
        f"    model asked for GBPUSD/SELL, got: {hijacked.instrument}/{hijacked.direction}"
    )
    print(f"    evidence still from the thesis:  {hijacked.evidence_refs[0]}")

    print("\n  Only a supported thesis may be proposed:")
    for stance in ("supported", "contested", "unsupported", "insufficient_evidence"):
        thesis = build_proposable_thesis(
            stance=stance,
            retained_conflicts=("Mean-reversion evidence disagrees.",)
            if stance == "contested"
            else (),
        )
        outcome = propose(thesis=thesis)
        verdict = "proposed" if outcome.status == "ok" else outcome.reasons[0]
        print(f"    {stance:<24} -> {verdict}")
    print(f"    proposable stances: {sorted(PROPOSABLE_STANCES)}")

    print("\n  The horizon and the window are bounded by the receiver's rule:")
    cases = (
        ("within the horizon", HORIZON, 1_800),
        ("the whole horizon", HORIZON, HORIZON),
        ("beyond the horizon", 600, 601),
        ("beyond the receiver bound", MAX_HORIZON_SECONDS + 1, 600),
    )
    for label, horizon, validity in cases:
        outcome = propose(horizon_seconds=horizon, validity_seconds=validity)
        verdict = "accepted" if outcome.status == "ok" else outcome.reasons[0]
        print(f"    {label:<26} -> {verdict}")


def fr_agentic_059() -> None:
    """Demonstrate the normal pipeline and the absence of a privileged route."""
    heading(
        "FR-AGENTIC-059",
        "Trade proposals enter the normal deterministic pipeline and receive "
        "no privileged route or reduced validation.",
    )

    proposal = propose().payload
    lineage = (PRINCIPAL, generate_id("req"), generate_id("wf"), generate_id("cor"))
    request = build_evaluation_request(proposal, *lineage)
    print(f"  receiver contract:   {request.schema_id}")
    print(f"  request identity:    {request.evaluation_request_id}")
    print(f"  idempotency key:     {request.idempotency_key}")
    print(f"  source digest:       {request.source_content_hash}")
    print(f"  direction carried:   {request.requested_direction}")
    print(f"  scope carried:       {request.evaluation_scope}")

    print("\n  The receiver derives its own identity; a caller cannot supply one:")
    for field in RECEIVER_DERIVED_FIELDS:
        try:
            create_strategy_proposal_evaluation_request(**{field: "forged"})
            verdict = "ERROR: a forged identity was accepted"
        except Exception as error:  # noqa: BLE001 - usage demonstrates rejection.
            verdict = str(error).splitlines()[0]
        print(f"    supplying {field:<22} -> {verdict}")

    print("\n  The same proposal always derives the same request identity:")
    again = build_evaluation_request(proposal, *lineage)
    print(
        f"    stable:  {again.evaluation_request_id == request.evaluation_request_id}"
    )
    other = build_evaluation_request(propose(direction="SELL").payload, *lineage)
    print(
        f"    differs on a different proposal: "
        f"{other.evaluation_request_id != request.evaluation_request_id}"
    )

    print("\n  The receiver's own contract has nowhere to put a broker field:")
    absent = [
        field
        for field in ("price", "quantity", "lot_size", "order_type", "venue", "account")
        if field not in type(request).model_fields
    ]
    print(f"    absent from the receiver request: {absent}")


def fr_agentic_060() -> None:
    """Demonstrate that the receiver's answer is the whole outcome."""
    heading(
        "FR-AGENTIC-060",
        "Receiver rejection, expiry, or acceptance is the outcome; a proposal "
        "receipt is never an order or a fill.",
    )

    proposal = propose().payload
    for status in ("accepted_for_evaluation", "rejected", "expired", "no_signal"):
        port = DeterministicIntake(
            receiver_result(status=status, signals_evaluated=0),
        )
        receipt = submit_trade_proposal(
            proposal,
            port,
            PRINCIPAL,
            generate_id("req"),
            generate_id("wf"),
            generate_id("cor"),
            at_time=NOW,
        )
        print(f"    {status:<26} -> intent produced: {receipt.intent_produced}")

    print("\n  An intent is recorded by identity, never by content:")
    port = DeterministicIntake(
        receiver_result(trade_intent_ref="strategy.trade_intent:intent-a"),
    )
    receipt = submit_trade_proposal(
        proposal,
        port,
        PRINCIPAL,
        generate_id("req"),
        generate_id("wf"),
        generate_id("cor"),
        at_time=NOW,
    )
    print(f"    intent_produced: {receipt.intent_produced}")
    print(f"    intent_ref:      {receipt.intent_ref}")
    print(f"    receipt fields:  {sorted(TradeProposalReceipt.model_fields)}")

    print("\n  A receipt cannot claim more than the receiver said:")
    cases = (
        (
            "a fill",
            {"status": "filled"},
        ),
        (
            "an intent on a rejection",
            {
                "status": "rejected",
                "signals_evaluated": 0,
                "intent_produced": True,
                "intent_ref": "strategy.trade_intent:intent-a",
            },
        ),
        (
            "an intent with no identity",
            {"intent_produced": True, "intent_ref": None},
        ),
        (
            "signals on an expired proposal",
            {
                "status": "expired",
                "intent_produced": False,
                "intent_ref": None,
                "signals_evaluated": 3,
            },
        ),
    )
    for label, override in cases:
        try:
            build_trade_proposal_receipt({**receipt.model_dump(), **override})
            verdict = "ERROR: an overclaiming receipt was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            verdict = "unbuildable"
        print(f"    {label:<32} -> {verdict}")

    print("\n  A result that does not answer this proposal is refused:")
    mismatched = MismatchedIntake()
    try:
        submit_trade_proposal(
            proposal,
            mismatched,
            PRINCIPAL,
            generate_id("req"),
            generate_id("wf"),
            generate_id("cor"),
            at_time=NOW,
        )
        verdict = "ERROR: a mismatched result was accepted"
    except ValueError as error:
        verdict = str(error)
    print(f"    {verdict}")

    print("\n  An expired proposal is never submitted at all:")
    short = propose(horizon_seconds=600, validity_seconds=60).payload
    port = DeterministicIntake()
    try:
        submit_trade_proposal(
            short,
            port,
            PRINCIPAL,
            generate_id("req"),
            generate_id("wf"),
            generate_id("cor"),
            at_time=NOW + timedelta(seconds=61),
        )
        verdict = "ERROR: an expired proposal reached the receiver"
    except ValueError as error:
        verdict = f"{error}; requests sent: {len(port.requests)}"
    print(f"    {verdict}")

    print("\n  A bounded operator view of the proposal:")
    for key, value in sorted(get_proposal_context(proposal).items()):
        print(f"    {key:<18} {value}")

    print(
        "\n  Note: no signal was evaluated and no intent constructed. The intake "
        "here is a\n  double, because evaluating a proposal needs a hash-bound "
        "SignalEvaluator,\n  a strategy config, point-in-time indicators, and an "
        "execution context: a full\n  Strategy composition a composition root "
        "owns. Steps 3 and 4 of WF-AGT-008\n  belong to Risk and Trading and are "
        "not reachable from this package."
    )


def main() -> None:
    """Run every functional-requirement demonstration for the trader."""
    fr_agentic_058()
    fr_agentic_059()
    fr_agentic_060()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-20", main)
