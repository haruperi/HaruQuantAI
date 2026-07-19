"""Immutable parameter-space contracts for Optimization."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import logger

type ParameterValue = bool | int | str | Decimal


class ParameterKind(StrEnum):
    """Supported underlying parameter value kinds."""

    INTEGER = "integer"
    FLOAT = "float"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    FIXED = "fixed"


class ParameterRange(BaseModel):
    """One bounded parameter definition with optional activation expression."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    kind: ParameterKind
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    step: Decimal | None = None
    choices: tuple[ParameterValue, ...] = ()
    fixed_value: ParameterValue | None = None
    active_when: str | None = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        """Validate a canonical parameter name.

        Args:
            value: Candidate parameter name.

        Returns:
            Validated name.

        Raises:
            ValueError: If the name is not a valid identifier.
        """
        logger.debug("Validating Optimization parameter name")
        if not value.isidentifier() or value.startswith("_"):
            raise ValueError("parameter name must be a public identifier")
        return value

    @field_validator("minimum", "maximum", "step")
    @classmethod
    def _validate_decimal(cls, value: Decimal | None) -> Decimal | None:
        """Reject non-finite range values.

        Args:
            value: Optional decimal boundary.

        Returns:
            The finite boundary or None.

        Raises:
            ValueError: If a supplied decimal is non-finite.
        """
        logger.debug("Validating Optimization decimal boundary")
        if value is not None and not value.is_finite():
            raise ValueError("parameter decimal values must be finite")
        return value

    @model_validator(mode="after")
    def _validate_definition(self) -> ParameterRange:  # noqa: C901
        """Validate fields applicable to the selected kind.

        Returns:
            Validated parameter range.

        Raises:
            ValueError: If the range definition is contradictory.
        """
        logger.debug("Validating Optimization parameter range definition")
        numeric = self.kind in {ParameterKind.INTEGER, ParameterKind.FLOAT}
        if numeric:
            if self.minimum is None or self.maximum is None or self.step is None:
                raise ValueError("numeric ranges require minimum, maximum, and step")
            if self.minimum > self.maximum or self.step <= 0:
                raise ValueError("numeric range bounds or step are invalid")
            if self.kind is ParameterKind.INTEGER and any(
                value != value.to_integral_value()
                for value in (self.minimum, self.maximum, self.step)
            ):
                raise ValueError("integer range values must be integral")
        elif any(
            value is not None for value in (self.minimum, self.maximum, self.step)
        ):
            raise ValueError("non-numeric ranges cannot define numeric boundaries")
        if self.kind is ParameterKind.CATEGORICAL:
            if not self.choices or len(set(self.choices)) != len(self.choices):
                raise ValueError("categorical choices must be non-empty and unique")
        elif self.choices:
            raise ValueError("only categorical parameters may define choices")
        if self.kind is ParameterKind.FIXED:
            if self.fixed_value is None:
                raise ValueError("fixed parameters require fixed_value")
        elif self.fixed_value is not None:
            raise ValueError("only fixed parameters may define fixed_value")
        if self.active_when is not None and (
            not self.active_when or self.active_when != self.active_when.strip()
        ):
            raise ValueError("active_when must be non-empty and trimmed")
        return self


class ParameterSpace(BaseModel):
    """A non-empty collection of uniquely named parameter definitions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    parameters: tuple[ParameterRange, ...]
    constraints: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_space(self) -> ParameterSpace:
        """Validate collection identity and constraint text.

        Returns:
            Validated parameter space.

        Raises:
            ValueError: If definitions are empty, duplicated, or malformed.
        """
        logger.debug("Validating Optimization parameter space contract")
        if not self.parameters:
            raise ValueError("parameter space must not be empty")
        names = tuple(item.name for item in self.parameters)
        if len(set(names)) != len(names):
            raise ValueError("parameter names must be unique")
        if any(not item or item != item.strip() for item in self.constraints):
            raise ValueError("constraints must be non-empty and trimmed")
        return self


__all__ = ["ParameterKind", "ParameterRange", "ParameterSpace", "ParameterValue"]
