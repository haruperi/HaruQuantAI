"""Instrument specifications, constraint validation, and broker alias mapping.

Feature:
    FEAT-DATA-INSTRUMENTS

Purpose:
    Provides authoritative financial instrument definitions, mathematical/financial
    constraint validation, tick/point sizing calculations, margin rates, and broker
    ticker alias resolution matching StrategyQuant X Instrument specifications.

Invariants:
    * Tick size, point value, and min volume must be strictly positive.
    * Decimals must be non-negative integers.
    * Max volume must be greater than or equal to min volume.
    * Symbols are normalized to uppercase for case-insensitive resolution.
    * Alias resolution is checked before direct catalog lookup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from app.contracts.data import (
    DATA_INSTRUMENTS,
    DATA_PERSISTENCE,
    BrokerAlias,
    DataPersistenceService,
    InstrumentDefinition,
    InstrumentValidationResult,
    InvalidInstrumentError,
)
from app.contracts.data import (
    InstrumentCatalog as IInstrumentCatalog,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(slots=True, frozen=True)
class InstrumentCatalogConfig:
    """Configuration for instrument catalog service."""

    strict_validation: bool = True


def _validate_sizes_and_points(inst: InstrumentDefinition) -> list[str]:
    """Validate tick, point, and precision invariants."""
    errors: list[str] = []
    if not inst.symbol or not inst.symbol.strip():
        errors.append("Symbol cannot be empty.")
    if inst.tick_size <= 0:
        errors.append(f"tick_size must be positive, got {inst.tick_size}")
    if inst.tick_step <= 0:
        errors.append(f"tick_step must be positive, got {inst.tick_step}")
    if inst.tick_value_in_money <= 0:
        errors.append(
            f"tick_value_in_money must be positive, got {inst.tick_value_in_money}"
        )
    if inst.point_value <= 0:
        errors.append(f"point_value must be positive, got {inst.point_value}")
    if inst.decimals < 0:
        errors.append(f"decimals cannot be negative, got {inst.decimals}")
    return errors


def _validate_volumes_and_margins(inst: InstrumentDefinition) -> list[str]:
    """Validate volumes, lot steps, and margin rate invariants."""
    errors: list[str] = []
    if inst.min_volume <= 0:
        errors.append(f"min_volume must be positive, got {inst.min_volume}")
    if inst.max_volume < inst.min_volume:
        errors.append(
            f"max_volume ({inst.max_volume}) cannot be less than "
            f"min_volume ({inst.min_volume})"
        )
    if inst.lot_step <= 0:
        errors.append(f"lot_step must be positive, got {inst.lot_step}")
    if inst.margin_rate < 0:
        errors.append(f"margin_rate cannot be negative, got {inst.margin_rate}")
    if inst.swap_3day_day not in range(7):
        errors.append(f"swap_3day_day must be in range 0..6, got {inst.swap_3day_day}")
    return errors


class InstrumentCatalogImpl(IInstrumentCatalog):
    """Concrete implementation of InstrumentCatalog protocol."""

    def __init__(
        self,
        persistence: DataPersistenceService,
        config: InstrumentCatalogConfig | None = None,
    ) -> None:
        """Initialize catalog service.

        Args:
            persistence: Persistence service for data domain storage.
            config: Optional configuration.
        """
        self._persistence = persistence
        self._config = config or InstrumentCatalogConfig()

    @override
    def validate_instrument(
        self, instrument: InstrumentDefinition
    ) -> InstrumentValidationResult:
        """Validate mathematical and financial constraints of an instrument."""
        errors: list[str] = []
        errors.extend(_validate_sizes_and_points(instrument))
        errors.extend(_validate_volumes_and_margins(instrument))
        return InstrumentValidationResult(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
        )

    @override
    async def get_instrument(self, symbol: str) -> InstrumentDefinition | None:
        """Retrieve instrument definition by canonical symbol or alias."""
        clean_symbol = symbol.strip().upper()
        canonical = await self._persistence.get_alias(clean_symbol)
        target = canonical or clean_symbol
        return await self._persistence.get_instrument(target)

    @override
    async def list_instruments(
        self, data_type: str | None = None
    ) -> list[InstrumentDefinition]:
        """List all instruments in the catalog, optionally filtered by type."""
        return await self._persistence.list_instruments(data_type=data_type)

    @override
    async def save_instrument(
        self, instrument: InstrumentDefinition
    ) -> InstrumentDefinition:
        """Persist or update an instrument definition after validation."""
        validation = self.validate_instrument(instrument)
        if not validation.is_valid and self._config.strict_validation:
            msg = f"Instrument validation failed: {'; '.join(validation.errors)}"
            raise InvalidInstrumentError(msg)
        return await self._persistence.save_instrument(instrument)

    @override
    async def delete_instrument(self, symbol: str) -> bool:
        """Delete an instrument definition from the catalog."""
        return await self._persistence.delete_instrument(symbol.strip().upper())

    @override
    async def resolve_alias(
        self, alias_or_symbol: str, broker_id: int | None = None
    ) -> str:
        """Translate a broker-specific alias to its canonical symbol."""
        clean = alias_or_symbol.strip().upper()
        canonical = await self._persistence.get_alias(clean, broker_id=broker_id)
        return canonical or clean

    @override
    async def add_alias(
        self, canonical: str, alias: str, broker_id: int = 0, notes: str = ""
    ) -> BrokerAlias:
        """Register a broker-specific symbol alias."""
        alias_dto = BrokerAlias(
            canonical_symbol=canonical.strip().upper(),
            alias_symbol=alias.strip().upper(),
            broker_id=broker_id,
            notes=notes,
        )
        return await self._persistence.save_alias(alias_dto)

    @override
    async def list_aliases(self, symbol: str | None = None) -> list[BrokerAlias]:
        """List all registered symbol aliases."""
        clean_sym = symbol.strip().upper() if symbol else None
        return await self._persistence.list_aliases(symbol=clean_sym)


SPEC: FeatureSpec = FeatureSpec(
    name="data.instruments",
    provides=frozenset({DATA_INSTRUMENTS}),
    requires=frozenset({DATA_PERSISTENCE}),
    optional=frozenset(),
    description="Authoritative instrument specifications, validation, and aliases.",
)


class InstrumentCatalogFeature:
    """Wire instrument catalog feature into kernel composition lifecycle."""

    def __init__(self, config: InstrumentCatalogConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional catalog configuration.
        """
        self._config = config or InstrumentCatalogConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve persistence and provide instrument catalog service.

        Args:
            context: Lifecycle feature context.
        """
        persistence = context.require(DATA_PERSISTENCE)
        service = InstrumentCatalogImpl(persistence, self._config)
        context.provide(DATA_INSTRUMENTS, service)
        logger.info("data_instruments_feature_started")


def feature() -> InstrumentCatalogFeature:
    """Return an unmounted InstrumentCatalogFeature instance.

    Returns:
        New InstrumentCatalogFeature instance.
    """
    return InstrumentCatalogFeature()


__all__ = [
    "SPEC",
    "InstrumentCatalogConfig",
    "InstrumentCatalogFeature",
    "InstrumentCatalogImpl",
    "feature",
]
