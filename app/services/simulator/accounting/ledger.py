"""Authoritative fixed-precision account ledger for Simulation."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.simulator.accounting.calculations import (
    ExecutionCostInput,
    ExecutionCostModel,
    SymbolSpecification,
    calculate_execution_costs,
    calculate_margin,
    normalize_volume,
)
from app.services.simulator.errors import SimulationError
from app.utils import logger


class LedgerFill(BaseModel):
    """Exact accounting effects supplied by one simulated fill."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: Literal["OPEN", "CLOSE"]
    side: Literal["BUY", "SELL"]
    volume: Decimal
    price: Decimal
    gross_profit: Decimal = Decimal(0)
    rollover_multiplier: Decimal = Decimal(0)
    margin_released: Decimal = Decimal(0)

    @field_validator("volume", "price")
    @classmethod
    def _validate_positive(cls, value: Decimal) -> Decimal:
        """Validate finite positive fill fields.

        Args:
            value: Candidate value.

        Returns:
            Validated value.

        Raises:
            ValueError: If invalid.
        """
        logger.debug("Validating positive Simulation ledger fill value")
        if not value.is_finite() or value <= 0:
            raise ValueError("Ledger fill volume and price must be finite and positive")
        return value

    @field_validator("gross_profit", "rollover_multiplier", "margin_released")
    @classmethod
    def _validate_finite(cls, value: Decimal, info: object) -> Decimal:
        """Validate finite fill effects and non-negative control values.

        Args:
            value: Candidate value.
            info: Pydantic field information.

        Returns:
            Validated value.

        Raises:
            ValueError: If invalid.
        """
        logger.debug("Validating Simulation ledger fill effect")
        if not value.is_finite():
            raise ValueError("Ledger fill effects must be finite")
        if str(getattr(info, "field_name", "")) != "gross_profit" and value < 0:
            raise ValueError("Ledger control effects must be non-negative")
        return value


class AccountLedger:
    """Mutable internal account authority with immutable public snapshots."""

    def __init__(
        self,
        initial_balance: Decimal,
        account_currency: str,
        symbol_specification: SymbolSpecification,
        cost_model: ExecutionCostModel,
    ) -> None:
        """Initialize one isolated Simulation account.

        Args:
            initial_balance: Positive starting cash balance.
            account_currency: Immutable account currency.
            symbol_specification: Approved symbol constraints.
            cost_model: Explicit execution-cost policy.

        Raises:
            SimulationError: If initial account evidence is invalid.
        """
        logger.info("Initializing Simulation account ledger")
        if not initial_balance.is_finite() or initial_balance <= 0:
            raise SimulationError(
                "SIM_INVALID_CONFIG", "Initial balance must be positive"
            )
        if not account_currency or account_currency != account_currency.strip():
            raise SimulationError("SIM_INVALID_CONFIG", "Account currency is invalid")
        self._balance = initial_balance
        self._used_margin = Decimal(0)
        self._unrealized = Decimal(0)
        self._commission_total = Decimal(0)
        self._swap_total = Decimal(0)
        self._gross_profit_total = Decimal(0)
        self._symbol_specification = symbol_specification
        self._cost_model = cost_model
        self._currency = account_currency

    def apply_fill(self, fill: LedgerFill) -> Mapping[str, Decimal]:
        """Atomically apply one fill's cash and margin effects.

        Args:
            fill: Validated simulated fill effects.

        Returns:
            Itemized commission, swap, and total costs charged by this fill, so
            the caller can attribute them to the exact position they belong to.

        Raises:
            SimulationError: If margin or account invariants would fail.
        """
        logger.info("Applying %s fill to Simulation ledger", fill.action)
        normalize_volume(fill.volume, self._symbol_specification)
        costs = calculate_execution_costs(
            ExecutionCostInput(
                volume=fill.volume,
                side=fill.side,
                rollover_multiplier=fill.rollover_multiplier,
            ),
            self._cost_model,
        )
        margin_delta = Decimal(0)
        if fill.action == "OPEN":
            margin_delta = calculate_margin(
                fill.volume,
                fill.price,
                self._symbol_specification.contract_size,
                self._symbol_specification.leverage,
            )
            projected_equity = self._balance + self._unrealized + costs["total"]
            if margin_delta > projected_equity - self._used_margin:
                raise SimulationError(
                    "SIM_INSUFFICIENT_MARGIN", "Free margin is insufficient"
                )
        elif fill.margin_released > self._used_margin:
            raise SimulationError(
                "SIM_ACCOUNT_INVARIANT_BROKEN", "Released margin exceeds used margin"
            )
        next_balance = self._balance + fill.gross_profit + costs["total"]
        next_margin = self._used_margin + margin_delta - fill.margin_released
        if not next_balance.is_finite() or next_margin < 0:
            raise SimulationError(
                "SIM_ACCOUNT_INVARIANT_BROKEN", "Account invariants would be broken"
            )
        self._balance = next_balance
        self._used_margin = next_margin
        self._commission_total += costs["commission"]
        self._swap_total += costs["swap"]
        self._gross_profit_total += fill.gross_profit
        return costs

    def mark_to_market(self, unrealized: Decimal) -> None:
        """Record aggregate open-position profit and loss at the current tick.

        Args:
            unrealized: Signed floating profit and loss of all open positions.

        Raises:
            SimulationError: If the supplied value is not finite.
        """
        logger.debug("Marking the Simulation account to market")
        if not unrealized.is_finite():
            raise SimulationError(
                "SIM_ACCOUNT_INVARIANT_BROKEN", "Unrealized value is not finite"
            )
        self._unrealized = unrealized

    def snapshot(self) -> Mapping[str, Decimal | str]:
        """Return an immutable read-only account snapshot.

        Returns:
            Immutable mapping of account values.

        Raises:
            SimulationError: If current state is inconsistent.
        """
        logger.debug("Creating immutable Simulation account snapshot")
        equity = self._balance + self._unrealized
        free_margin = equity - self._used_margin
        if any(
            not value.is_finite()
            for value in (
                self._balance,
                self._used_margin,
                self._unrealized,
                equity,
                free_margin,
                self._commission_total,
                self._swap_total,
                self._gross_profit_total,
            )
        ):
            raise SimulationError(
                "SIM_ACCOUNT_INVARIANT_BROKEN", "Account state is non-finite"
            )
        return MappingProxyType(
            {
                "balance": self._balance,
                "equity": equity,
                "used_margin": self._used_margin,
                "free_margin": free_margin,
                "unrealized": self._unrealized,
                "commission": self._commission_total,
                "swap": self._swap_total,
                "gross_profit": self._gross_profit_total,
                "account_currency": self._currency,
            }
        )


__all__ = ["AccountLedger", "LedgerFill"]
