"""Immutable concrete signal and point-in-time signal-evidence contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, cast

from pydantic import (
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.data.contracts import MarketDataset  # noqa: TC001
from app.services.strategy.contracts._base import (
    JsonValue,
    _Contract,
    _finite_decimal,
    _freeze_json,
    _hash,
    _text,
    _thaw_json,
    _utc,
)
from app.utils import logger


class StrategySignal(_Contract):
    """Immutable deterministic output from one concrete signal evaluator."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.signal.v1"] = "strategy.signal.v1"
    signal_id: str
    strategy_id: str
    strategy_version: str
    symbol: str
    timestamp: datetime
    signal_name: str
    side: Literal["BUY", "SELL"] | None
    active: bool
    lineage: Mapping[str, str]
    facts: Mapping[str, JsonValue]

    @field_validator("signal_id")
    @classmethod
    def _validate_signal_id(cls, value: str) -> str:
        """Validate deterministic signal identity.

        Args:
            value: Signal SHA-256 identity.

        Returns:
            Validated lowercase digest.
        """
        logger.debug("Validating concrete Strategy signal identity")
        return _hash(value)

    @field_validator("strategy_id", "strategy_version", "symbol", "signal_name")
    @classmethod
    def _validate_signal_text(cls, value: str) -> str:
        """Validate required signal text.

        Args:
            value: Text to validate.

        Returns:
            Validated bounded text.
        """
        logger.debug("Validating concrete Strategy signal text")
        return _text(value)

    @field_validator("timestamp")
    @classmethod
    def _validate_signal_time(cls, value: datetime) -> datetime:
        """Validate the point-in-time signal timestamp.

        Args:
            value: Signal timestamp.

        Returns:
            Validated aware UTC timestamp.
        """
        logger.debug("Validating concrete Strategy signal timestamp")
        return _utc(value)

    @field_validator("lineage", mode="after")
    @classmethod
    def _freeze_signal_lineage(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze signal lineage references.

        Args:
            value: Lineage mapping.

        Returns:
            Immutable validated lineage.
        """
        logger.debug("Freezing concrete Strategy signal lineage")
        return MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )

    @field_validator("facts", mode="after")
    @classmethod
    def _freeze_signal_facts(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze JSON-compatible signal facts.

        Args:
            value: Signal fact mapping.

        Returns:
            Immutable signal facts.
        """
        logger.debug("Freezing concrete Strategy signal facts")
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_serializer("lineage", when_used="json")
    def _serialize_signal_lineage(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize immutable signal lineage.

        Args:
            value: Immutable lineage mapping.

        Returns:
            Ordinary lineage mapping.
        """
        logger.debug("Serializing concrete Strategy signal lineage")
        return dict(value)

    @field_serializer("facts", when_used="json")
    def _serialize_signal_facts(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize immutable signal facts.

        Args:
            value: Immutable signal fact mapping.

        Returns:
            JSON-compatible fact mapping.
        """
        logger.debug("Serializing concrete Strategy signal facts")
        return cast("dict[str, object]", _thaw_json(value))


class StrategySignalEvidence(_Contract):
    """Immutable point-in-time evidence for concrete signal evaluation."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.signal_evidence.v1"] = "strategy.signal_evidence.v1"
    evidence_id: str
    primary_market: MarketDataset
    related_markets: Mapping[str, MarketDataset]
    point_size: Decimal
    feature_values: Mapping[str, tuple[Decimal, ...]]
    feature_available_at: Mapping[str, datetime]
    feature_refs: Mapping[str, str]
    active_position_tags: tuple[str, ...]

    @field_validator("evidence_id")
    @classmethod
    def _validate_evidence_id(cls, value: str) -> str:
        """Validate signal evidence identity.

        Args:
            value: Evidence identifier.

        Returns:
            Validated bounded identifier.
        """
        logger.debug("Validating concrete Strategy signal evidence identity")
        return _text(value)

    @field_validator("point_size")
    @classmethod
    def _validate_point_size(cls, value: Decimal) -> Decimal:
        """Validate explicit positive point-size evidence.

        Args:
            value: Market point size.

        Returns:
            Validated positive finite point size.

        Raises:
            ValueError: If the point size is non-finite or non-positive.
        """
        logger.debug("Validating concrete Strategy point-size evidence")
        validated = _finite_decimal(value)
        if validated is None or validated <= 0:
            raise ValueError("point_size must be positive")
        return validated

    @field_validator("related_markets", mode="after")
    @classmethod
    def _freeze_related_markets(
        cls, value: Mapping[str, MarketDataset]
    ) -> Mapping[str, MarketDataset]:
        """Freeze named related market datasets.

        Args:
            value: Named point-in-time market datasets.

        Returns:
            Immutable related market mapping.
        """
        logger.debug("Freezing related concrete Strategy market evidence")
        return MappingProxyType({_text(key): item for key, item in value.items()})

    @field_validator("feature_values", mode="after")
    @classmethod
    def _freeze_feature_values(
        cls, value: Mapping[str, tuple[Decimal, ...]]
    ) -> Mapping[str, tuple[Decimal, ...]]:
        """Validate and freeze named feature values.

        Args:
            value: Named decimal feature sequences.

        Returns:
            Immutable validated feature values.

        Raises:
            ValueError: If a feature value is non-finite.
        """
        logger.debug("Freezing concrete Strategy feature values")
        frozen: dict[str, tuple[Decimal, ...]] = {}
        for key, items in value.items():
            validated_items: list[Decimal] = []
            for item in items:
                validated = _finite_decimal(item)
                if validated is None:
                    raise ValueError("feature values must be finite")
                validated_items.append(validated)
            frozen[_text(key)] = tuple(validated_items)
        return MappingProxyType(frozen)

    @field_validator("feature_available_at", mode="after")
    @classmethod
    def _freeze_feature_times(
        cls, value: Mapping[str, datetime]
    ) -> Mapping[str, datetime]:
        """Validate and freeze feature availability timestamps.

        Args:
            value: Named feature availability timestamps.

        Returns:
            Immutable UTC timestamp mapping.
        """
        logger.debug("Freezing concrete Strategy feature availability")
        return MappingProxyType({_text(key): _utc(item) for key, item in value.items()})

    @field_validator("feature_refs", mode="after")
    @classmethod
    def _freeze_feature_refs(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze feature provenance references.

        Args:
            value: Named feature provenance references.

        Returns:
            Immutable validated reference mapping.
        """
        logger.debug("Freezing concrete Strategy feature references")
        return MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )

    @field_validator("active_position_tags")
    @classmethod
    def _validate_position_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate immutable active position ownership tags.

        Args:
            value: Position tags supplied by the runtime owner.

        Returns:
            Validated unique tags.

        Raises:
            ValueError: If position tags are duplicated.
        """
        logger.debug("Validating concrete Strategy active position tags")
        validated = tuple(_text(item) for item in value)
        if len(set(validated)) != len(validated):
            raise ValueError("active_position_tags must be unique")
        return validated

    @model_validator(mode="after")
    def _validate_feature_completeness(self) -> StrategySignalEvidence:
        """Require values, availability, and provenance for every feature.

        Returns:
            Validated complete signal evidence.

        Raises:
            ValueError: If feature evidence keys disagree.
        """
        logger.debug("Validating concrete Strategy feature completeness")
        keys = set(self.feature_values)
        if keys != set(self.feature_available_at) or keys != set(self.feature_refs):
            raise ValueError("feature evidence values, times, and refs must align")
        return self

    @field_serializer("related_markets", when_used="json")
    def _serialize_related_markets(
        self, value: Mapping[str, MarketDataset]
    ) -> dict[str, MarketDataset]:
        """Serialize named related markets.

        Args:
            value: Immutable related markets.

        Returns:
            Ordinary related-market mapping.
        """
        logger.debug("Serializing related concrete Strategy market evidence")
        return dict(value)

    @field_serializer("feature_values", when_used="json")
    def _serialize_feature_values(
        self, value: Mapping[str, tuple[Decimal, ...]]
    ) -> dict[str, tuple[Decimal, ...]]:
        """Serialize named feature values.

        Args:
            value: Immutable feature values.

        Returns:
            Ordinary feature-value mapping.
        """
        logger.debug("Serializing concrete Strategy feature values")
        return dict(value)

    @field_serializer("feature_available_at", when_used="json")
    def _serialize_feature_times(
        self, value: Mapping[str, datetime]
    ) -> dict[str, datetime]:
        """Serialize feature availability timestamps.

        Args:
            value: Immutable feature timestamps.

        Returns:
            Ordinary feature timestamp mapping.
        """
        logger.debug("Serializing concrete Strategy feature availability")
        return dict(value)

    @field_serializer("feature_refs", when_used="json")
    def _serialize_feature_refs(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize feature provenance references.

        Args:
            value: Immutable feature references.

        Returns:
            Ordinary feature reference mapping.
        """
        logger.debug("Serializing concrete Strategy feature references")
        return dict(value)
