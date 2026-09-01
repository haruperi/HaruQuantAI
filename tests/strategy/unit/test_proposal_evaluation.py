"""External proposal evaluation behavior tests."""

import importlib
from datetime import timedelta

import pytest
from app.composition.logging import get_logger
from app.services.strategy import create_strategy_signal, evaluate_strategy_proposal

from tests.strategy.unit.test_models import (
    HASH,
    NOW,
    make_config,
    make_context,
    make_ref,
)
from tests.strategy.unit.test_proposal_contracts import make_proposal_request
from tests.strategy.unit.test_proposal_validation import _dependencies

logger = get_logger(__name__)


def _signal(*, side: str = "BUY", active: bool = True, name: str = "entry") -> object:
    """Build one deterministic evaluator signal."""
    return create_strategy_signal(
        signal_id=HASH if name == "entry" else "b" * 64,
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        symbol="EURUSD",
        timestamp=NOW - timedelta(minutes=1),
        signal_name=name,
        side=side,
        active=active,
        lineage={"market": "dataset-1"},
        facts={"observed_close": "1.1000"},
    )


def _patch_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    signals: tuple[object, ...],
) -> None:
    """Patch external boundaries while retaining proposal decision logic."""
    module = importlib.import_module("app.services.strategy.proposal_intake.evaluation")
    monkeypatch.setattr(
        module,
        "_validate_strategy_proposal",
        lambda *_args: (make_ref(), make_config()),
    )
    monkeypatch.setattr(
        module,
        "evaluate_strategy_signals",
        lambda *_args: signals,
    )
    monkeypatch.setattr(
        module,
        "unwrap_strategy_response",
        lambda value, **_: getattr(value, "data", value),
    )
    monkeypatch.setattr(module, "persist_audit_event", lambda event: event)


def _evaluate(monkeypatch: pytest.MonkeyPatch, signals: tuple[object, ...]) -> object:
    """Evaluate one proposal with focused deterministic dependencies."""
    _patch_dependencies(monkeypatch, signals)
    auth, ref, config, policy, evidence, evaluator = _dependencies()
    return evaluate_strategy_proposal(
        make_proposal_request(),
        auth,
        ref,
        config,
        policy,
        evidence,
        (object(),),
        make_context(),
        evaluator,
    )


def test_evaluation_builds_intent_from_matching_active_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify accepted proposals produce a canonical lineage-bound intent."""
    logger.debug("Testing accepted external proposal evaluation")
    outcome = _evaluate(monkeypatch, (_signal(),))
    assert outcome.data is not None
    result = outcome.data
    assert result.status == "accepted_for_evaluation"
    assert result.trade_intent is not None
    assert result.trade_intent.symbol == "EURUSD"
    assert result.trade_intent.side == "BUY"
    assert result.trade_intent.quantity_hint is None
    assert result.trade_intent.lineage["source_content_hash"] == HASH
    assert result.audit_event_ref is not None


@pytest.mark.parametrize(
    ("signals", "status", "reason"),
    [
        ((), "no_signal", "NO_ACTIVE_SIGNAL"),
        ((_signal(side="SELL"),), "no_signal", "REQUEST_DIRECTION_NOT_SUPPORTED"),
        (
            (_signal(), _signal(name="second")),
            "rejected",
            "AMBIGUOUS_ACTIVE_SIGNALS",
        ),
    ],
)
def test_evaluation_returns_typed_non_acceptance(
    monkeypatch: pytest.MonkeyPatch,
    signals: tuple[object, ...],
    status: str,
    reason: str,
) -> None:
    """Verify missing, opposing, and ambiguous signals remain non-executable."""
    logger.debug("Testing non-accepted external proposal evaluation")
    outcome = _evaluate(monkeypatch, signals)
    assert outcome.data is not None
    assert outcome.data.status == status
    assert outcome.data.reason_codes == (reason,)
    assert outcome.data.trade_intent is None
