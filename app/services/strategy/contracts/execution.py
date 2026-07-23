"""Fixed evaluation context, typed events, decisions, and atomic results."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, cast

from pydantic import (
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.strategy.contracts._base import (
    JsonValue,
    _Contract,
    _freeze_json,
    _hash,
    _text,
    _thaw_json,
    _utc,
)
from app.services.strategy.contracts.enums import (  # noqa: TC001
    StrategyEnvironment,
    StrategyTimingPolicy,
)
from app.utils import logger


class StrategyExecutionContext(_Contract):
    """Immutable deterministic evaluation context."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.execution_context.v1"] = (
        "strategy.execution_context.v1"
    )
    environment: StrategyEnvironment
    decision_timestamp: datetime
    timing_policy: StrategyTimingPolicy
    seed: int
    interface_version: str
    request_id: str
    workflow_id: str
    correlation_id: str
    dependency_status: Mapping[str, JsonValue]
    snapshot_refs: tuple[str, ...]
    max_diagnostic_bytes: int = Field(gt=0)

    @field_validator("interface_version", "request_id", "workflow_id", "correlation_id")
    @classmethod
    def _validate_context_text(cls, value: str) -> str:
        """Validate context text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy execution context text")
        return _text(value)

    @field_validator("decision_timestamp")
    @classmethod
    def _validate_context_time(cls, value: datetime) -> datetime:
        """Validate decision time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Strategy decision timestamp")
        return _utc(value)

    @field_validator("dependency_status", mode="after")
    @classmethod
    def _freeze_dependency_status(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze dependency status evidence.

        Args:
            value: Dependency evidence.

        Returns:
            Validated evidence.
        """
        logger.debug("Freezing Strategy dependency status")
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_serializer("dependency_status", when_used="json")
    def _serialize_dependency_status(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize immutable dependency evidence.

        Args:
            value: Immutable dependency evidence.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy dependency status")
        thawed = _thaw_json(value)
        return cast("dict[str, object]", thawed)


class StrategyEvent(_Contract):
    """Receiver-owned immutable external event evidence."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.event.v1"] = "strategy.event.v1"
    event_type: str
    hook: str
    occurred_at: datetime
    sequence: int = Field(ge=0)
    source_owner: str
    source_contract_version: str
    source_schema_id: str
    source_snapshot_ref: str
    source_checksum: str
    source_as_of: datetime
    facts: Mapping[str, JsonValue]
    request_id: str
    workflow_id: str
    correlation_id: str

    @field_validator(
        "event_type",
        "hook",
        "source_owner",
        "source_contract_version",
        "source_schema_id",
        "source_snapshot_ref",
        "request_id",
        "workflow_id",
        "correlation_id",
    )
    @classmethod
    def _validate_event_text(cls, value: str) -> str:
        """Validate event evidence text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy event text")
        return _text(value)

    @field_validator("source_checksum")
    @classmethod
    def _validate_event_checksum(cls, value: str) -> str:
        """Validate source checksum.

        Args:
            value: Hash to validate.

        Returns:
            Validated hash.
        """
        logger.debug("Validating Strategy event checksum")
        return _hash(value)

    @field_validator("occurred_at", "source_as_of")
    @classmethod
    def _validate_event_time(cls, value: datetime) -> datetime:
        """Validate event evidence time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Strategy event timestamp")
        return _utc(value)

    @field_validator("facts", mode="after")
    @classmethod
    def _freeze_event_facts(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze bounded event facts.

        Args:
            value: Fact mapping.

        Returns:
            Validated facts.
        """
        logger.debug("Freezing Strategy event facts")
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_serializer("facts", when_used="json")
    def _serialize_event_facts(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize immutable event facts.

        Args:
            value: Immutable event facts.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy event facts")
        return cast("dict[str, object]", _thaw_json(value))


def _validate_strategy_order_shape(
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] | None,
    limit_price: Decimal | None,
    stop_price: Decimal | None,
) -> None:
    """Validate explicit Strategy execution-instruction shape.

    Args:
        order_type: Optional proposal order type.
        limit_price: Optional limit entry price.
        stop_price: Optional stop entry price.

    Raises:
        ValueError: If prices are invalid or conflict with the order type.
    """
    logger.debug("Validating Strategy decision order shape")
    required_prices = {
        "MARKET": (False, False),
        "LIMIT": (True, False),
        "STOP": (False, True),
        "STOP_LIMIT": (True, True),
    }
    if order_type is not None:
        limit_required, stop_required = required_prices[order_type]
        if (limit_price is not None) != limit_required:
            raise ValueError("limit_price conflicts with order_type")
        if (stop_price is not None) != stop_required:
            raise ValueError("stop_price conflicts with order_type")
    for price in (limit_price, stop_price):
        if price is not None and (not price.is_finite() or price <= 0):
            raise ValueError("entry prices must be finite and positive")


class StrategyDecision(_Contract):
    """Neutral or actionable evaluator decision."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.decision.v1"] = "strategy.decision.v1"
    decision_id: str
    sequence: int = Field(ge=0)
    action: Literal["NEUTRAL", "PROPOSE"]
    symbol: str | None = None
    side: Literal["BUY", "SELL"] | None = None
    intent_type: (
        Literal["OPEN", "CLOSE", "REDUCE", "INCREASE", "MODIFY", "CANCEL"] | None
    ) = None
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: Literal["GTC", "IOC", "FOK", "GTD", "DAY"] | None = None
    requested_sizing_mode: str | None = None
    quantity_hint: Decimal | None = None
    notional_hint: Decimal | None = None
    valid_from: datetime
    expires_at: datetime
    parent_intent_id: str | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    allow_partial_fills: bool
    min_fill_size: Decimal | None = None
    rationale_ref: str | None = None
    lineage: Mapping[str, str]
    rationale_refs: tuple[str, ...]
    diagnostic_facts: Mapping[str, JsonValue]
    candidate_local_state: Mapping[str, JsonValue] | None = None

    @field_validator("diagnostic_facts", "candidate_local_state", mode="after")
    @classmethod
    def _freeze_decision_json(
        cls, value: Mapping[str, JsonValue] | None
    ) -> Mapping[str, JsonValue] | None:
        """Freeze decision-owned JSON mappings.

        Args:
            value: Optional JSON mapping.

        Returns:
            Optional immutable mapping.
        """
        logger.debug("Freezing Strategy decision JSON material")
        if value is None:
            return None
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_validator("lineage", mode="after")
    @classmethod
    def _freeze_decision_lineage(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze decision lineage.

        Args:
            value: Decision lineage.

        Returns:
            Immutable lineage mapping.
        """
        logger.debug("Freezing Strategy decision lineage")
        return MappingProxyType(dict(value))

    @field_validator("decision_id")
    @classmethod
    def _validate_decision_id(cls, value: str) -> str:
        """Validate decision identity.

        Args:
            value: Identity text.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy decision identity")
        return _text(value)

    @field_validator("valid_from", "expires_at")
    @classmethod
    def _validate_decision_time(cls, value: datetime) -> datetime:
        """Validate decision time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Strategy decision timestamp")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_decision(self) -> StrategyDecision:
        """Validate neutral and proposal invariants.

        Returns:
            The validated decision.

        Raises:
            ValueError: If decision fields conflict.
        """
        logger.debug("Validating Strategy decision relationships")
        if self.expires_at <= self.valid_from:
            raise ValueError("expires_at must follow valid_from")
        action_fields = (
            self.symbol,
            self.side,
            self.intent_type,
            self.order_type,
            self.limit_price,
            self.stop_price,
            self.time_in_force,
            self.quantity_hint,
            self.notional_hint,
        )
        if self.action == "NEUTRAL" and any(item is not None for item in action_fields):
            raise ValueError("neutral decisions cannot contain proposal fields")
        if self.action == "PROPOSE" and (
            self.symbol is None
            or self.side is None
            or self.intent_type is None
            or self.order_type is None
        ):
            raise ValueError(
                "proposal decisions require symbol, side, intent type, and order type"
            )
        _validate_strategy_order_shape(
            self.order_type,
            self.limit_price,
            self.stop_price,
        )
        if self.quantity_hint is not None and self.quantity_hint <= 0:
            raise ValueError("quantity_hint must be positive")
        if self.notional_hint is not None and self.notional_hint <= 0:
            raise ValueError("notional_hint must be positive")
        if self.min_fill_size is not None and (
            not self.allow_partial_fills or self.min_fill_size <= 0
        ):
            raise ValueError("min_fill_size requires allowed partial fills")
        return self

    @field_serializer("diagnostic_facts", "candidate_local_state", when_used="json")
    def _serialize_decision_json(
        self, value: Mapping[str, JsonValue] | None
    ) -> dict[str, object] | None:
        """Serialize immutable decision JSON mappings.

        Args:
            value: Optional immutable mapping.

        Returns:
            Optional ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy decision JSON material")
        if value is None:
            return None
        return cast("dict[str, object]", _thaw_json(value))

    @field_serializer("lineage", when_used="json")
    def _serialize_decision_lineage(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize immutable decision lineage.

        Args:
            value: Immutable lineage.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy decision lineage")
        return dict(value)


class StrategyExecutionResult(_Contract):
    """Atomic ordered evaluation output."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.execution_result.v1"] = "strategy.execution_result.v1"
    decisions: tuple[StrategyDecision, ...]
    intents: tuple[object, ...]
    diagnostics: object
    replay_manifest: object
    local_state_update: Mapping[str, JsonValue] | None = None
    result_hash: str

    @field_validator("result_hash")
    @classmethod
    def _validate_result_hash(cls, value: str) -> str:
        """Validate the result hash.

        Args:
            value: Hash to validate.

        Returns:
            Validated hash.
        """
        logger.debug("Validating Strategy execution result hash")
        return _hash(value)

    @model_validator(mode="after")
    def _validate_atomic_result(self) -> StrategyExecutionResult:
        """Validate deterministic ordering and atomicity.

        Returns:
            The validated result.

        Raises:
            ValueError: If decision ordering or batch correspondence is invalid.
        """
        logger.debug("Validating atomic Strategy execution result")
        sequences = tuple(decision.sequence for decision in self.decisions)
        if sequences != tuple(sorted(sequences)) or len(set(sequences)) != len(
            sequences
        ):
            raise ValueError("decisions must have unique ascending sequence numbers")
        proposal_count = sum(
            decision.action == "PROPOSE" for decision in self.decisions
        )
        if proposal_count != len(self.intents):
            raise ValueError("every proposal must produce exactly one intent")
        return self

    @field_serializer("local_state_update", when_used="json")
    def _serialize_local_state_update(
        self, value: Mapping[str, JsonValue] | None
    ) -> dict[str, object] | None:
        """Serialize optional immutable result local state.

        Args:
            value: Optional local state.

        Returns:
            Optional ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy result local state")
        if value is None:
            return None
        return cast("dict[str, object]", _thaw_json(value))
