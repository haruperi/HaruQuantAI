"""Unit tests for control action primitives."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.services.trading.actions.controls import (
    pause_strategy,
    resume_strategy,
    shutdown,
    sync_positions,
    trigger_global_kill_switch,
    trigger_strategy_kill_switch,
    trigger_symbol_kill_switch,
)
from app.services.trading.contracts import (
    PromotionStage,
    SideEffectMode,
    TradingResponseEnvelope,
    TradingRoute,
    TradingStatus,
)
from app.services.trading.security.error_mapping import TradingMappedError

from tests.trading.unit.actions._fixtures import (
    ROUTE_KWARGS,
    FakeEventJournal,
    FakeIdempotencyStore,
    as_dict,
    build_deps,
)


def test_pause_and_resume_strategy_are_local_only() -> None:
    """pause_strategy/resume_strategy never mark a broker mutation attempt."""
    deps = build_deps()
    paused = pause_strategy(
        strategy_id="strat-1",
        reason="incident",
        request_id="req-1",
        correlation_id="corr-1",
        deps=deps,
        **ROUTE_KWARGS,
    )
    resumed = resume_strategy(
        strategy_id="strat-1",
        reason="cleared",
        request_id="req-2",
        correlation_id="corr-2",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert paused.status is TradingStatus.SUCCESS
    assert paused.side_effect_mode is SideEffectMode.NONE
    assert resumed.status is TradingStatus.SUCCESS


def test_pause_strategy_rejects_blank_inputs() -> None:
    """pause_strategy rejects a blank strategy_id or reason."""
    deps = build_deps()
    with pytest.raises(TradingMappedError):
        pause_strategy(
            strategy_id=" ",
            reason="incident",
            request_id="req-1",
            correlation_id="corr-1",
            deps=deps,
            **ROUTE_KWARGS,
        )
    with pytest.raises(TradingMappedError):
        pause_strategy(
            strategy_id="strat-1",
            reason=" ",
            request_id="req-2",
            correlation_id="corr-2",
            deps=deps,
            **ROUTE_KWARGS,
        )


def test_sync_positions_is_read_only_and_persists_when_store_injected() -> None:
    """sync_positions reads broker state and persists via the trade store."""
    deps = build_deps()
    response = sync_positions(
        route=TradingRoute.SIM,
        request_id="req-3",
        correlation_id="corr-3",
        deps=deps,
    )
    assert response.status is TradingStatus.SUCCESS
    assert response.side_effect_mode is SideEffectMode.NONE
    assert "positions" in response.data
    assert "orders" in response.data


def test_shutdown_rejects_negative_pending_count() -> None:
    """shutdown rejects a negative in-flight request count."""
    deps = build_deps()
    with pytest.raises(TradingMappedError):
        shutdown(pending_request_count=-1, deps=deps)


def test_shutdown_runs_flush_callback_and_journals() -> None:
    """shutdown runs the flush callback and journals a shutdown event."""
    journal = FakeEventJournal()
    deps = build_deps(event_journal=journal)
    flushed = {"called": False}

    def flush() -> None:
        flushed["called"] = True

    result = shutdown(pending_request_count=2, deps=deps, flush=flush)
    assert result.pending_request_count == 2
    assert result.flushed is True
    assert flushed["called"] is True
    # No reconcile callback was supplied, so nothing was reconciled. This field
    # previously reported True unconditionally (BF-TRD-005).
    assert result.reconciliation_triggered is False
    assert len(journal.events) == 1


def test_shutdown_without_flush_callback() -> None:
    """shutdown tolerates a missing flush callback."""
    deps = build_deps()
    result = shutdown(pending_request_count=0, deps=deps)
    assert result.flushed is False


def test_shutdown_reports_reconciliation_only_when_it_runs() -> None:
    """reconciliation_triggered must reflect reality, not intent."""
    deps = build_deps()
    calls: list[str] = []
    result = shutdown(
        pending_request_count=0, deps=deps, reconcile=lambda: calls.append("ran")
    )
    assert calls == ["ran"]
    assert result.reconciliation_triggered is True


def test_shutdown_reports_false_when_reconciliation_raises() -> None:
    """A failed reconciliation must not be reported as a successful one."""
    deps = build_deps()

    def boom() -> None:
        raise RuntimeError("broker unreachable")

    result = shutdown(pending_request_count=0, deps=deps, reconcile=boom)
    assert result.reconciliation_triggered is False


def test_shutdown_drains_in_flight_requests() -> None:
    """shutdown reports whether in-flight work actually drained."""
    deps = build_deps()
    result = shutdown(pending_request_count=3, deps=deps, drain=lambda _timeout: True)
    assert result.drained is True


def test_shutdown_reports_undrained_requests() -> None:
    deps = build_deps()
    result = shutdown(pending_request_count=3, deps=deps, drain=lambda _timeout: False)
    assert result.drained is False


def test_shutdown_drain_defaults_to_zero_pending() -> None:
    deps = build_deps()
    assert shutdown(pending_request_count=0, deps=deps).drained is True
    assert shutdown(pending_request_count=1, deps=deps).drained is False


@pytest.mark.parametrize(
    ("trigger_fn", "kwargs"),
    [
        (trigger_global_kill_switch, {}),
        (trigger_strategy_kill_switch, {"strategy_id": "strat-1"}),
        (trigger_symbol_kill_switch, {"symbol": "EURUSD"}),
    ],
)
def test_kill_switch_triggers_are_idempotent_audited_and_journaled(
    trigger_fn: Callable[..., TradingResponseEnvelope],
    kwargs: dict[str, str],
) -> None:
    """Kill switch triggers dedupe by scope and always journal an event."""
    store = FakeIdempotencyStore()
    journal = FakeEventJournal()
    deps = build_deps(idempotency_store=store, event_journal=journal)
    first = trigger_fn(
        reason="incident",
        actor="operator-1",
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        request_id="req-a",
        correlation_id="corr-a",
        deps=deps,
        idempotency_store=store,
        event_journal=journal,
        **kwargs,
    )
    second = trigger_fn(
        reason="incident-repeat",
        actor="operator-1",
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        request_id="req-b",
        correlation_id="corr-b",
        deps=deps,
        idempotency_store=store,
        event_journal=journal,
        **kwargs,
    )
    assert first.status is TradingStatus.ACCEPTED
    assert as_dict(first.data["reservation"])["decision"] == "reserved"
    assert as_dict(second.data["reservation"])["decision"] == "duplicate"
    assert len(journal.events) == 2
    assert first.audit_ref == "journal-1"


def test_kill_switch_triggers_reject_blank_reason_or_actor() -> None:
    """Kill switch triggers reject a blank reason or actor."""
    store = FakeIdempotencyStore()
    journal = FakeEventJournal()
    deps = build_deps(idempotency_store=store, event_journal=journal)
    with pytest.raises(TradingMappedError):
        trigger_global_kill_switch(
            reason=" ",
            actor="operator-1",
            route=TradingRoute.LIVE,
            promotion_stage=PromotionStage.MICRO_LIVE,
            request_id="req-1",
            correlation_id="corr-1",
            deps=deps,
            idempotency_store=store,
            event_journal=journal,
        )
    with pytest.raises(TradingMappedError):
        trigger_global_kill_switch(
            reason="incident",
            actor=" ",
            route=TradingRoute.LIVE,
            promotion_stage=PromotionStage.MICRO_LIVE,
            request_id="req-2",
            correlation_id="corr-2",
            deps=deps,
            idempotency_store=store,
            event_journal=journal,
        )


def test_strategy_and_symbol_kill_switch_reject_blank_scope() -> None:
    """Strategy/symbol kill switches reject a blank scope identifier."""
    store = FakeIdempotencyStore()
    journal = FakeEventJournal()
    deps = build_deps(idempotency_store=store, event_journal=journal)
    with pytest.raises(TradingMappedError):
        trigger_strategy_kill_switch(
            strategy_id=" ",
            reason="incident",
            actor="operator-1",
            route=TradingRoute.LIVE,
            promotion_stage=PromotionStage.MICRO_LIVE,
            request_id="req-1",
            correlation_id="corr-1",
            deps=deps,
            idempotency_store=store,
            event_journal=journal,
        )
    with pytest.raises(TradingMappedError):
        trigger_symbol_kill_switch(
            symbol=" ",
            reason="incident",
            actor="operator-1",
            route=TradingRoute.LIVE,
            promotion_stage=PromotionStage.MICRO_LIVE,
            request_id="req-2",
            correlation_id="corr-2",
            deps=deps,
            idempotency_store=store,
            event_journal=journal,
        )
