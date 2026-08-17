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
from app.services.simulator.errors import SimulationError, operation_guard
from app.utils import get_logger

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)


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

    @operation_guard(
        operation="simulation.accounting.account_ledger.apply_fill",
        risk_level="medium",
        read_only=False,
    )
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
        return self.apply_fill_internal(fill)

    def apply_fill_internal(self, fill: LedgerFill) -> Mapping[str, Decimal]:
        """Apply one already boundary-validated fill inside Simulation.

        Args:
            fill: Validated simulated fill effects.

        Returns:
            Itemized signed cash effects.

        Raises:
            SimulationError: If margin or account invariants would fail.
        """
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

    @operation_guard(
        operation="simulation.accounting.account_ledger.mark_to_market",
        risk_level="medium",
        read_only=False,
    )
    def mark_to_market(self, unrealized: Decimal) -> None:
        """Record aggregate open-position profit and loss at the current tick.

        Args:
            unrealized: Signed floating profit and loss of all open positions.

        Raises:
            SimulationError: If the supplied value is not finite.
        """
        self.mark_to_market_internal(unrealized)

    def mark_to_market_internal(self, unrealized: Decimal) -> None:
        """Record one already boundary-validated floating PnL value.

        Args:
            unrealized: Signed aggregate floating PnL.

        Raises:
            SimulationError: If the supplied value is non-finite.
        """
        if not unrealized.is_finite():
            raise SimulationError(
                "SIM_ACCOUNT_INVARIANT_BROKEN", "Unrealized value is not finite"
            )
        self._unrealized = unrealized

    def calculate_profit(
        self,
        *,
        side: Literal["BUY", "SELL"],
        volume: Decimal,
        entry_price: Decimal,
        exit_price: Decimal,
    ) -> Decimal:
        """Value an FX price movement using the configured contract size.

        Args:
            side: Position direction.
            volume: Position volume in lots.
            entry_price: Position opening price.
            exit_price: Current or closing price.

        Returns:
            Signed account-currency profit before costs.

        Raises:
            SimulationError: If any calculation input is invalid.
        """
        normalize_volume(volume, self._symbol_specification)
        for value, field in ((entry_price, "entry_price"), (exit_price, "exit_price")):
            if not value.is_finite() or value <= 0:
                raise SimulationError(
                    "SIM_INVALID_CONFIG", f"{field} must be finite and positive"
                )
        direction = Decimal(1) if side == "BUY" else Decimal(-1)
        return (
            direction
            * (exit_price - entry_price)
            * self._symbol_specification.contract_size
            * volume
        )

    @operation_guard(
        operation="simulation.accounting.account_ledger.snapshot",
        risk_level="medium",
        read_only=True,
    )
    def snapshot(self) -> Mapping[str, Decimal | str]:
        """Return an immutable read-only account snapshot.

        Returns:
            Immutable mapping of account values.

        Raises:
            SimulationError: If current state is inconsistent.
        """
        return self.snapshot_internal()

    def snapshot_internal(self) -> Mapping[str, Decimal | str]:
        """Return the trusted internal immutable account projection.

        Returns:
            Immutable mapping of current account values.

        Raises:
            SimulationError: If current state is inconsistent.
        """
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
