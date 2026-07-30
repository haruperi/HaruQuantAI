"""FEAT-STR-11 full Strategy-owned proposal evaluation workflow."""

from datetime import timedelta
from pathlib import Path

from app.services.data import run_data_migrations
from app.services.strategy import (
    create_strategy_config,
    create_strategy_ref,
    create_strategy_signal,
    evaluate_strategy_proposal,
    get_strategy_environment,
    register_strategy_version,
)
from app.utils import generate_id, get_logger

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import (
    COR,
    HASH,
    NOW,
    REQ,
    make_auth,
    make_context,
    make_market,
    make_policy,
    make_signal_evidence,
)
from tests.strategy.unit.test_proposal_contracts import make_proposal_request

logger = get_logger(__name__)


class _EvidenceEvaluator:
    """Deterministic evaluator producing a signal from the supplied market."""

    strategy_id = "mean-reversion"
    strategy_version = "1.0.0"
    module_path = "approved.strategies.mean_reversion"
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH

    def evaluate_signals(
        self,
        evidence: object,
        indicators: tuple[object, ...],
        config: object,
        context: object,
    ) -> tuple[object, ...]:
        """Return one traceable active signal from real contract evidence."""
        del indicators, config
        market = evidence.primary_market
        last = market.records[-1]
        return (
            create_strategy_signal(
                signal_id=HASH,
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                symbol=market.symbol,
                timestamp=last.available_at,
                signal_name="integration-market-observation",
                side="BUY",
                active=True,
                lineage={"dataset_request_id": market.request_id},
                facts={
                    "close": str(last.close),
                    "decision_at": str(context.decision_timestamp),
                },
            ),
        )


def test_registered_proposal_evaluation_persists_audit_and_builds_intent(
    tmp_path: Path,
) -> None:
    """Register, validate, evaluate, audit, and emit one canonical intent."""
    logger.debug("Testing complete external proposal intake")
    market = make_market((("1", "2", "0.5", "1.4"), ("1.4", "2", "1", "1.8")))
    context = make_context()
    auth = make_auth().model_copy(
        update={
            "permissions": (
                "strategy:register",
                "strategy:evaluate_proposal",
            ),
            "scopes": ("strategy:proposal_evaluation",),
        }
    )
    ref = create_strategy_ref(
        strategy_id="mean-reversion",
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=REQ,
        correlation_id=COR,
    )
    config = create_strategy_config(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"period": 5},
        request_id=REQ,
    )
    with storage_context(tmp_path):
        data_migration = run_data_migrations(generate_id("req"))
        assert data_migration.data is not None
        registration = register_strategy_version(
            make_registration(),
            auth,
            make_policy(),
        )
        outcome = evaluate_strategy_proposal(
            make_proposal_request(),
            auth,
            ref,
            config,
            make_policy(),
            make_signal_evidence(market),
            (),
            context,
            _EvidenceEvaluator(),
        )
    assert registration.data is not None
    assert registration.data.status == "ACCEPTED"
    assert outcome.data is not None
    assert outcome.data.status == "accepted_for_evaluation"
    assert outcome.data.trade_intent is not None
    assert outcome.data.trade_intent.signal_timestamp == NOW - timedelta(minutes=55)
    assert outcome.data.evaluated_signals[0].lineage["dataset_request_id"] == REQ
    assert outcome.data.trade_intent.lineage["source_content_hash"] == HASH
    assert outcome.data.audit_event_ref is not None
    assert outcome.metadata.modifies_database is True
