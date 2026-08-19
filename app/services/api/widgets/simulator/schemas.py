"""Simulator gateway request schemas."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.services.api.contracts.models import _BaseApiContract, _validate_non_empty

_MAX_PARAMETERS = 32
_MAX_PARAMETER_LENGTH = 64
_MAX_BAR_LIMIT = 1_000_000
_CURRENCY_CODE_LENGTH = 3

BarTimeframe = Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]


class SimulatorRunRequest(_BaseApiContract):
    """Operator-chosen configuration for one canonical backtest run.

    Every hash, provider revision, and tick lineage the Simulator requires is
    derived server-side from genuine provider evidence. A client supplies only
    the choices a human actually makes.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.simulator_run_request.v1"] = "api.simulator_run_request.v1"
    symbol: str = Field(min_length=1, max_length=32)
    timeframe: BarTimeframe = "H1"
    start: datetime
    end: datetime
    strategy_id: str = Field(min_length=1, max_length=100)
    parameters: Mapping[str, str] = Field(default_factory=dict)
    initial_balance: Decimal = Field(default=Decimal("10000.00"), gt=0)
    account_currency: str = Field(default="USD", min_length=3, max_length=3)
    volume: Decimal = Field(default=Decimal("0.1"), gt=0)
    commission_per_lot_per_side: Decimal = Field(default=Decimal(7), ge=0)
    spread_points: Decimal = Field(default=Decimal(10), ge=0)
    slippage_points: Decimal = Field(default=Decimal(1), ge=0)
    seed: int = Field(default=7, ge=0)
    bar_limit: int = Field(default=10_000, gt=0, le=_MAX_BAR_LIMIT)

    @field_validator("symbol", "strategy_id")
    @classmethod
    def _validate_identifier(cls, value: str) -> str:
        """Validate one trimmed non-empty identifier.

        Returns:
            Validated identifier.
        """
        return _validate_non_empty(value, "identifier")

    @field_validator("account_currency")
    @classmethod
    def _validate_currency(cls, value: str) -> str:
        """Validate one three-letter uppercase currency code.

        Returns:
            Normalized currency code.

        Raises:
            ValueError: If the code is not three ASCII letters.
        """
        normalized = value.strip().upper()
        if not normalized.isalpha() or len(normalized) != _CURRENCY_CODE_LENGTH:
            raise ValueError("account_currency must be three letters")
        return normalized

    @field_validator("parameters")
    @classmethod
    def _validate_parameters(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate a bounded strategy parameter override mapping.

        Returns:
            Validated parameter mapping.

        Raises:
            ValueError: If the mapping or any entry exceeds its bound.
        """
        if len(value) > _MAX_PARAMETERS:
            message = f"at most {_MAX_PARAMETERS} parameters are accepted"
            raise ValueError(message)
        for name, item in value.items():
            if not name.strip() or len(name) > _MAX_PARAMETER_LENGTH:
                raise ValueError("parameter names must be bounded and non-empty")
            if len(item) > _MAX_PARAMETER_LENGTH:
                raise ValueError("parameter values must be bounded")
        return value

    @model_validator(mode="after")
    def _validate_window(self) -> SimulatorRunRequest:
        """Require a forward-ordered measurement window.

        Returns:
            The validated request.

        Raises:
            ValueError: If the window is not forward-ordered.
        """
        if self.start >= self.end:
            raise ValueError("start must be earlier than end")
        return self


__all__ = ("BarTimeframe", "SimulatorRunRequest")
