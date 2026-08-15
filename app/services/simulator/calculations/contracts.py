"""Private immutable effective-dated calculation contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Literal

_SHA256_LENGTH = 64
_MAX_CURRENCY_DIGITS = 12


def _decimal(value: object, name: str, *, positive: bool = False) -> Decimal:
    """Return one finite exact Decimal.

    Args:
        value: Candidate Decimal or canonical numeric string.
        name: Stable field name.
        positive: Whether zero and negative values are forbidden.

    Returns:
        Validated Decimal.

    Raises:
        TypeError: If the value is a binary float.
        ValueError: If the value is not exact, finite, or positive as required.
    """
    if isinstance(value, float):
        message = f"{name} cannot be float"
        raise TypeError(message)
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        message = f"{name} must be Decimal-compatible"
        raise ValueError(message) from error
    if not result.is_finite() or (positive and result <= 0):
        message = f"{name} is invalid"
        raise ValueError(message)
    return result


@dataclass(frozen=True, slots=True, kw_only=True)
class CalculationSpecification:
    """One effective MT5-FX calculation specification."""

    revision_id: str
    checksum: str
    effective_from: datetime
    effective_to: datetime | None
    calculation_mode: Literal["FOREX"]
    contract_size: Decimal
    point: Decimal
    tick_size: Decimal
    tick_value: Decimal | None
    base_currency: str
    profit_currency: str
    margin_currency: str
    leverage: Decimal
    margin_initial: Decimal | None
    margin_maintenance: Decimal | None
    margin_hedged: Decimal | None
    margin_hedged_use_leg: bool
    account_currency: str
    currency_digits: int
    rounding_rule: Literal["ROUND_HALF_EVEN", "ROUND_HALF_UP"]

    def __post_init__(self) -> None:  # noqa: C901
        """Validate specification identity, interval, and exact scalars.

        Raises:
            ValueError: If any specification invariant is invalid.
        """
        for name in (
            "revision_id",
            "base_currency",
            "profit_currency",
            "margin_currency",
            "account_currency",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                message = f"{name} must be non-empty text"
                raise ValueError(message)
        if len(self.checksum) != _SHA256_LENGTH:
            raise ValueError("specification checksum must be SHA-256")
        if self.calculation_mode != "FOREX":
            raise ValueError("only FOREX calculation mode is supported")
        for value in (self.effective_from, self.effective_to):
            if value is not None and (
                value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value)
            ):
                raise ValueError("effective bounds must be aware UTC")
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective interval must be positive")
        for name in ("contract_size", "point", "tick_size", "leverage"):
            object.__setattr__(
                self, name, _decimal(getattr(self, name), name, positive=True)
            )
        for name in (
            "tick_value",
            "margin_initial",
            "margin_maintenance",
            "margin_hedged",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _decimal(value, name))
        if not 0 <= self.currency_digits <= _MAX_CURRENCY_DIGITS:
            raise ValueError("currency_digits must be between zero and twelve")

    def covers(self, as_of: datetime) -> bool:
        """Return whether this half-open revision covers an instant.

        Args:
            as_of: Aware-UTC calculation instant.

        Returns:
            True when the instant is inside the revision interval.
        """
        return self.effective_from <= as_of and (
            self.effective_to is None or as_of < self.effective_to
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CalculationArtifact:
    """Validated offline conformance artifact."""

    model_identity: str
    cases: tuple[Mapping[str, str], ...]
    checksum: str

    def __post_init__(self) -> None:
        """Freeze artifact cases.

        Raises:
            ValueError: If the artifact is empty or checksum malformed.
        """
        if not self.model_identity or not self.cases:
            raise ValueError("conformance artifact identity and cases are required")
        if len(self.checksum) != _SHA256_LENGTH:
            raise ValueError("artifact checksum must be SHA-256")
        object.__setattr__(
            self,
            "cases",
            tuple(MappingProxyType(dict(case)) for case in self.cases),
        )


__all__ = ["CalculationArtifact", "CalculationSpecification", "_decimal"]
