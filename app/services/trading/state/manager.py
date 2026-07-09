"""Local trading state update coordinators."""
# ruff: noqa: TC001

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.trading.contracts import JsonObject, TradingRoute
from app.services.trading.state.event_journal import (
    AppendOnlyEventJournal,
    JournalEvent,
)
from app.services.trading.state.ports import Clock, TradingStateStore
from app.utils.logger import logger


class StateUpdateResult(BaseModel):
    """Result of a local state update."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state_ref: str
    journal_event: JournalEvent
    snapshot: JsonObject

    @model_validator(mode="after")
    def validate_result(self) -> StateUpdateResult:
        """Validate state update result.

        Returns:
            StateUpdateResult: Validated result.
        """
        logger.info("Validated state update result {}.", self.state_ref)
        return self


class LocalStateManager:
    """Coordinator for local state updates and journal writes."""

    def __init__(
        self,
        *,
        state_store: TradingStateStore,
        journal: AppendOnlyEventJournal,
        clock: Clock,
    ) -> None:
        """Initialize a local state manager.

        Args:
            state_store: Injected state store.
            journal: Append-only event journal.
            clock: Injected clock.
        """
        logger.info("Initializing local trading state manager.")
        self._state_store = state_store
        self._journal = journal
        self._clock = clock

    def apply_state_update(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        account_id: str,
        symbol: str,
        request_id: str,
        correlation_id: str,
        actor: str,
        event_type: str,
        update: JsonObject,
        expected_version: int | None,
    ) -> StateUpdateResult:
        """Persist a local state update and append its journal event.

        Args:
            route: Trading route.
            tenant_id: Tenant namespace.
            account_id: Account identifier.
            symbol: Symbol identifier.
            request_id: Request identifier.
            correlation_id: Correlation identifier.
            actor: Actor identifier.
            event_type: Journal event type.
            update: State update payload.
            expected_version: Optimistic concurrency version.

        Returns:
            StateUpdateResult: Persisted state and journal references.
        """
        logger.info("Applying local trading state update {}.", request_id)
        snapshot: JsonObject = {
            "id": request_id,
            "updated_at": self._clock.now_utc().isoformat(),
            "account_id": account_id,
            "symbol": symbol,
            "update": update,
        }
        state_ref = self._state_store.save_state(
            route=route,
            tenant_id=tenant_id,
            snapshot=snapshot,
            expected_version=expected_version,
        )
        event = self._journal.append_event(
            event_type=event_type,
            request_id=request_id,
            correlation_id=correlation_id,
            route=route,
            account_id=account_id,
            symbol=symbol,
            actor=actor,
            payload={"state_ref": state_ref, "snapshot": snapshot},
        )
        return StateUpdateResult(
            state_ref=state_ref,
            journal_event=event,
            snapshot=snapshot,
        )
