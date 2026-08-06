"""Unit tests for signals/boundary.py branch coverage floor."""

from unittest.mock import patch

from app.services.strategy import (
    create_strategy_evaluator,
    create_strategy_signal,
    evaluate_and_record_strategy_signals,
    list_strategy_signals,
    mark_strategy_signal_submitted,
    record_strategy_signals,
)

from tests.strategy.unit.test_models import (
    HASH,
    NOW,
    REQ,
    make_context,
    make_market,
    make_ref,
    make_signal_config,
    make_signal_evidence,
)


def make_signal() -> object:
    return create_strategy_signal(
        signal_id=HASH,
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        symbol="EURUSD",
        signal_name="BUY_SIGNAL",
        side="BUY",
        active=True,
        timestamp=NOW,
        lineage={"bars": "10"},
        facts={"atr": "0.0012"},
    )


def test_record_strategy_signals_and_list() -> None:
    """Verify recording and listing strategy signals."""
    sig = make_signal()
    with patch(
        "app.services.strategy.persistence.create_strategy_signal_records"
    ) as mock_create:
        res = record_strategy_signals(
            config_id="cfg-1",
            signals=(sig,),
            intents=(),
            request_id=REQ,
            correlation_id="cor-1",
        )
        assert res.status == "success"
        assert res.data is not None
        assert len(res.data) == 1
        assert mock_create.called

    with patch(
        "app.services.strategy.persistence.read_strategy_signals",
        return_value=(),
    ) as mock_read:
        res_list = list_strategy_signals("cfg-1", publication_status="generated")
        assert res_list.status == "success"
        assert mock_read.called


def test_mark_strategy_signal_submitted_failure() -> None:
    """Verify mark_strategy_signal_submitted error branch when update fails."""
    with patch(
        "app.services.strategy.persistence.update_strategy_signal_publication_record",
        return_value=False,
    ):
        res = mark_strategy_signal_submitted(
            signal_id="sig-1",
            expected_status="generated",
            risk_submission_ref="risk-1",
            request_id=REQ,
            correlation_id="cor-1",
        )
        assert res.status == "error"
        assert res.error is not None
        assert res.error.code == "STRATEGY_INTERNAL_ERROR"


def test_evaluate_and_record_strategy_signals_flow() -> None:
    """Verify evaluate_and_record_strategy_signals executes evaluation and persistence."""
    ref = make_ref()
    config = make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20})
    market = make_market(prices=[("1.1000", "1.1050", "1.0950", "1.1020")])
    evidence = make_signal_evidence(market)
    context = make_context()
    evaluator = create_strategy_evaluator(
        "random_walk",
        strategy_id=ref.manifest.strategy_id,
        strategy_version=ref.manifest.strategy_version,
        module_path=ref.manifest.module_path,
        source_hash=ref.manifest.source_hash,
        artifact_hash=ref.manifest.artifact_hash,
        dependency_hash=ref.manifest.dependency_hash,
    )

    with patch(
        "app.services.strategy.signals.boundary.record_strategy_signals"
    ) as mock_rec:
        res = evaluate_and_record_strategy_signals(
            ref, config, "cfg-1", evidence, (), context, evaluator
        )
        assert res.status == "success"
        assert res.data is not None
        assert isinstance(res.data, tuple)
        assert mock_rec.called
