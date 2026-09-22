"""Bounded immutable value and descriptor vocabulary for the shared plugin metamodel."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, override

MAX_VALUE_DEPTH = 16
MAX_COLLECTION_SIZE = 10_000
MAX_KEY_LENGTH = 128
MAX_STRING_LENGTH = 65_536
MAX_IDENTIFIER_LENGTH = 64
MAX_TOTAL_ELEMENTS = 100_000
KEY_VALUE_PAIR_LENGTH = 2
INT_MIN = -9_007_199_254_740_991  # -2^53 + 1 (JavaScript safe integer lower bound)
INT_MAX = 9_007_199_254_740_991  # 2^53 - 1 (JavaScript safe integer upper bound)

IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_identifier(name: str, field_name: str = "Identifier") -> str:
    """Validate that a string is a bounded lowercase identifier.

    Args:
        name: Name to validate.
        field_name: Context label for error messages.

    Returns:
        The validated name.
    """
    if not isinstance(name, str):
        raise TypeError(f"{field_name} must be a string, got {type(name).__name__}")
    if (
        not name
        or len(name) > MAX_IDENTIFIER_LENGTH
        or not IDENTIFIER_PATTERN.match(name)
    ):
        raise ValueError(
            f"{field_name} must be non-empty lowercase <= "
            f"{MAX_IDENTIFIER_LENGTH} chars matching ^[a-z][a-z0-9_]*$: {name!r}"
        )
    return name


@dataclass(frozen=True, slots=True)
class MissingValue:
    """Explicit missing value marker, distinct from None / JSON null."""

    reason: str = ""

    def __post_init__(self) -> None:
        """Validate bounded reason length."""
        if not isinstance(self.reason, str):
            raise TypeError("MissingValue reason must be a string")
        if len(self.reason) > MAX_STRING_LENGTH:
            raise ValueError(
                f"MissingValue reason exceeds max length {MAX_STRING_LENGTH}"
            )


type ScalarValue = bool | int | float | str | MissingValue | None
type Value = ScalarValue | FrozenArray | FrozenObject


@dataclass(frozen=True, slots=True)
class FrozenArray(Sequence[Value]):
    """Immutable sequence wrapper for schema and parameter values."""

    items: tuple[Value, ...] = ()

    def __post_init__(self) -> None:
        """Validate collection bounds and items."""
        if not isinstance(self.items, tuple):
            raise TypeError("FrozenArray items must be a tuple")
        if len(self.items) > MAX_COLLECTION_SIZE:
            raise ValueError(f"FrozenArray size exceeds limit {MAX_COLLECTION_SIZE}")

    @override
    def __len__(self) -> int:
        """Return the number of items in the array."""
        return len(self.items)

    @override
    def __getitem__(self, index: Any) -> Any:
        """Return item or slice."""
        return self.items[index]

    @override
    def __iter__(self) -> Iterator[Value]:
        """Iterate over items."""
        return iter(self.items)

    @override
    def __repr__(self) -> str:
        """Return string representation."""
        return f"FrozenArray({list(self.items)!r})"


@dataclass(frozen=True, slots=True)
class FrozenObject(Mapping[str, Value]):
    """Immutable mapping wrapper with sorted keys and duplicate rejection."""

    entries: tuple[tuple[str, Value], ...] = ()

    def __post_init__(self) -> None:
        """Validate sorted pairs, bounded size, and unique keys."""
        if not isinstance(self.entries, tuple):
            raise TypeError("FrozenObject entries must be a tuple of pairs")
        if len(self.entries) > MAX_COLLECTION_SIZE:
            raise ValueError(
                f"FrozenObject size {len(self.entries)} "
                f"exceeds max {MAX_COLLECTION_SIZE}"
            )
        seen: set[str] = set()
        prev_key: str | None = None
        for pair in self.entries:
            if not isinstance(pair, tuple) or len(pair) != KEY_VALUE_PAIR_LENGTH:
                raise TypeError(
                    "FrozenObject entries must contain 2-tuples of (key, value)"
                )
            key, _ = pair
            if not isinstance(key, str):
                raise TypeError(
                    f"FrozenObject keys must be strings, got {type(key).__name__}"
                )
            if len(key) > MAX_KEY_LENGTH or not key:
                raise ValueError(
                    f"Key must be non-empty and <= {MAX_KEY_LENGTH} chars: {key!r}"
                )
            if key in seen:
                raise ValueError(f"Duplicate key in FrozenObject: {key!r}")
            if prev_key is not None and key < prev_key:
                raise ValueError(
                    f"FrozenObject keys must be sorted: {prev_key!r} > {key!r}"
                )
            seen.add(key)
            prev_key = key

    @override
    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)

    @override
    def __iter__(self) -> Iterator[str]:
        """Iterate over keys."""
        for key, _ in self.entries:
            yield key

    @override
    def __getitem__(self, key: str) -> Value:
        """Get value by key."""
        for k, v in self.entries:
            if k == key:
                return v
        raise KeyError(key)

    @override
    def __contains__(self, key: object) -> bool:
        """Check whether key exists."""
        if not isinstance(key, str):
            return False
        return any(k == key for k, _ in self.entries)

    @override
    def __repr__(self) -> str:
        """Return string representation."""
        return f"FrozenObject({list(self.entries)!r})"

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> FrozenObject:
        """Create a FrozenObject from any mapping, sorting keys automatically."""
        pairs = [(k, freeze_value(v)) for k, v in mapping.items()]
        pairs.sort(key=lambda p: p[0])
        return cls(tuple(pairs))

    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[str, Any]]) -> FrozenObject:
        """Create a FrozenObject from an iterable of key-value pairs."""
        frozen_pairs = [(k, freeze_value(v)) for k, v in pairs]
        frozen_pairs.sort(key=lambda p: p[0])
        return cls(tuple(frozen_pairs))

    def to_dict(self) -> dict[str, Any]:
        """Convert to regular dict for serialization or reading."""
        return dict(self.entries)


EMPTY_FROZEN_OBJECT = FrozenObject()
EMPTY_FROZEN_ARRAY = FrozenArray()


def _freeze_scalar(val: Any) -> ScalarValue:
    """Validate and return scalar value."""
    if val is None or isinstance(val, (bool, MissingValue)):
        return val
    if isinstance(val, int):
        if not (INT_MIN <= val <= INT_MAX):
            raise ValueError(
                f"Integer value {val} outside safe bounds [{INT_MIN}, {INT_MAX}]"
            )
        return val
    if isinstance(val, float):
        if not math.isfinite(val):
            raise ValueError(f"Float value must be finite, got {val}")
        return val
    if isinstance(val, str):
        if len(val) > MAX_STRING_LENGTH:
            raise ValueError(
                f"String length {len(val)} exceeds max {MAX_STRING_LENGTH}"
            )
        return val
    return None


def freeze_value(val: Any, depth: int = 0) -> Value:
    """Recursively freeze and validate values into portable immutable forms.

    Args:
        val: Value to freeze.
        depth: Current recursion depth.

    Returns:
        Frozen immutable representation of val.

    Raises:
        ValueError: If depth, collection size, or the total frozen element
            count exceeds its bound.
    """
    return _freeze_counted(val, depth, [0])


def _freeze_counted(val: Any, depth: int, counter: list[int]) -> Value:
    """Freeze with a shared total-element counter across the whole tree."""
    counter[0] += 1
    if counter[0] > MAX_TOTAL_ELEMENTS:
        raise ValueError(
            f"Total frozen element count exceeds limit of {MAX_TOTAL_ELEMENTS}"
        )
    if depth > MAX_VALUE_DEPTH:
        raise ValueError(f"Value nesting depth exceeds limit of {MAX_VALUE_DEPTH}")
    if val is None or isinstance(val, (bool, int, float, str, MissingValue)):
        return _freeze_scalar(val)
    if isinstance(val, (FrozenObject, FrozenArray)):
        return val
    if isinstance(val, Mapping):
        pairs: list[tuple[str, Value]] = []
        for k, v in val.items():
            if not isinstance(k, str):
                raise TypeError(f"Mapping keys must be strings, got {type(k).__name__}")
            pairs.append((k, _freeze_counted(v, depth + 1, counter)))
        pairs.sort(key=lambda p: p[0])
        return FrozenObject(tuple(pairs))
    if isinstance(val, (list, tuple, Sequence)) and not isinstance(val, (str, bytes)):
        return FrozenArray(
            tuple(_freeze_counted(item, depth + 1, counter) for item in val)
        )
    raise TypeError(
        f"Unsupported leaf value type for freeze_value: {type(val).__name__}"
    )


class ValueKind(StrEnum):
    """Supported data types for ports and parameters."""

    BOOLEAN = "boolean"
    INTEGER = "integer"
    NUMBER = "number"
    TEXT = "text"
    ENUM = "enum"
    OBJECT = "object"
    ALIGNED_SERIES = "aligned_series"


class Unit(StrEnum):
    """Standard measurement units for inputs and outputs."""

    NONE = "none"
    PERCENT = "percent"
    CURRENCY = "currency"
    POINTS = "points"
    SECONDS = "seconds"
    BARS = "bars"
    RATIO = "ratio"


class Alignment(StrEnum):
    """Series time/index alignment specification."""

    NONE = "none"
    INDEX = "index"
    TIMESTAMP = "timestamp"
    BAR_INDEX = "bar_index"


@dataclass(frozen=True, slots=True)
class NumericConstraint:
    """Numeric validity constraints independent of optimization domains."""

    min_value: float | int | None = None
    max_value: float | int | None = None
    step: float | int | None = None
    allow_negative: bool = True

    def __post_init__(self) -> None:
        """Validate numeric constraints."""
        for name, val in (
            ("min_value", self.min_value),
            ("max_value", self.max_value),
            ("step", self.step),
        ):
            if val is not None:
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise TypeError(f"NumericConstraint {name} must be int or float")
                if not math.isfinite(val):
                    raise ValueError(f"NumericConstraint {name} must be finite")
        if self.step is not None and self.step <= 0:
            raise ValueError(f"NumericConstraint step must be > 0, got {self.step}")
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError(
                f"NumericConstraint min_value {self.min_value} > "
                f"max_value {self.max_value}"
            )
        if (
            not self.allow_negative
            and self.min_value is not None
            and self.min_value < 0
        ):
            raise ValueError(
                "min_value cannot be negative when allow_negative is False"
            )

    def validate(self, val: Any) -> list[str]:
        """Validate a single numeric value against constraints.

        Args:
            val: Value to validate.

        Returns:
            List of issue messages, empty if valid.
        """
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            return [f"Expected numeric value, got {type(val).__name__}"]
        if not math.isfinite(val):
            return ["Value must be finite"]
        issues: list[str] = []
        if not self.allow_negative and val < 0:
            issues.append(f"Value {val} cannot be negative")
        if self.min_value is not None and val < self.min_value:
            issues.append(f"Value {val} is below minimum {self.min_value}")
        if self.max_value is not None and val > self.max_value:
            issues.append(f"Value {val} is above maximum {self.max_value}")
        return issues


@dataclass(frozen=True, slots=True)
class TextConstraint:
    """Text validity constraints."""

    min_length: int = 0
    max_length: int = 256
    pattern: str | None = None

    def __post_init__(self) -> None:
        """Validate text constraint properties."""
        if not isinstance(self.min_length, int) or self.min_length < 0:
            raise ValueError("min_length must be a non-negative integer")
        if (
            not isinstance(self.max_length, int)
            or self.max_length < self.min_length
            or self.max_length > MAX_STRING_LENGTH
        ):
            raise ValueError(
                f"max_length must be between min_length ({self.min_length}) and "
                f"{MAX_STRING_LENGTH}"
            )
        if self.pattern is not None:
            if not isinstance(self.pattern, str) or not self.pattern:
                raise ValueError("pattern must be a non-empty regex string")
            try:
                re.compile(self.pattern)
            except re.error as err:
                raise ValueError(
                    f"Invalid regex pattern {self.pattern!r}: {err}"
                ) from err

    def validate(self, val: Any) -> list[str]:
        """Validate a single text value against constraints.

        Args:
            val: Value to validate.

        Returns:
            List of issue messages, empty if valid.
        """
        if not isinstance(val, str):
            return [f"Expected string value, got {type(val).__name__}"]
        issues: list[str] = []
        if len(val) < self.min_length:
            issues.append(
                f"String length {len(val)} is below minimum {self.min_length}"
            )
        if len(val) > self.max_length:
            issues.append(f"String length {len(val)} exceeds maximum {self.max_length}")
        if self.pattern is not None and not re.search(self.pattern, val):
            issues.append(f"String does not match pattern {self.pattern!r}")
        return issues


@dataclass(frozen=True, slots=True)
class EnumChoice:
    """Choice definition for enum parameters."""

    value: str
    label: str
    description: str = ""

    def __post_init__(self) -> None:
        """Validate choice values."""
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("EnumChoice value must be a non-empty string")
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("EnumChoice label must be a non-empty string")
        if not isinstance(self.description, str):
            raise TypeError("EnumChoice description must be a string")


@dataclass(frozen=True, slots=True)
class EnumConstraint:
    """Enum validity constraints."""

    choices: tuple[EnumChoice, ...]

    def __post_init__(self) -> None:
        """Validate unique, non-empty choices."""
        if not isinstance(self.choices, tuple) or not self.choices:
            raise ValueError(
                "EnumConstraint choices must be a non-empty tuple of EnumChoice"
            )
        seen: set[str] = set()
        for choice in self.choices:
            if not isinstance(choice, EnumChoice):
                raise TypeError("EnumConstraint choices must be EnumChoice instances")
            if choice.value in seen:
                raise ValueError(f"Duplicate enum choice value: {choice.value!r}")
            seen.add(choice.value)

    def validate(self, val: Any) -> list[str]:
        """Validate a value against enum choices.

        Args:
            val: Value to validate.

        Returns:
            List of issue messages, empty if valid.
        """
        if not isinstance(val, str):
            return [f"Expected enum string value, got {type(val).__name__}"]
        if not any(c.value == val for c in self.choices):
            valid = [c.value for c in self.choices]
            return [f"Value {val!r} is not a valid choice in {valid}"]
        return []


class OptimizationScale(StrEnum):
    """Distribution scale for parameter search/optimization."""

    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    STEP = "step"


class OptimizationDistribution(StrEnum):
    """Sampling distribution for parameter search/optimization."""

    UNIFORM = "uniform"
    NORMAL = "normal"


def _validate_opt_bounds(
    min_val: float | None,
    max_val: float | None,
    step: float | None,
    scale: OptimizationScale,
) -> None:
    """Validate optimization search bounds."""
    if step is not None and step <= 0:
        raise ValueError(f"OptimizationDomain step must be > 0, got {step}")
    if min_val is not None and max_val is not None and min_val > max_val:
        raise ValueError(
            f"OptimizationDomain min_value {min_val} > max_value {max_val}"
        )
    if scale == OptimizationScale.LOGARITHMIC and min_val is not None and min_val <= 0:
        raise ValueError("Logarithmic scale requires min_value > 0")


@dataclass(frozen=True, slots=True)
class OptimizationDomain:
    """Optimization search bounds and distribution for parameter search."""

    eligible: bool = True
    min_value: float | int | None = None
    max_value: float | int | None = None
    step: float | int | None = None
    scale: OptimizationScale = OptimizationScale.LINEAR
    distribution: OptimizationDistribution = OptimizationDistribution.UNIFORM

    def __post_init__(self) -> None:
        """Validate optimization bounds."""
        if not isinstance(self.eligible, bool):
            raise TypeError("OptimizationDomain eligible must be a bool")
        if not isinstance(self.scale, OptimizationScale):
            raise TypeError("OptimizationDomain scale must be an OptimizationScale")
        if not isinstance(self.distribution, OptimizationDistribution):
            raise TypeError(
                "OptimizationDomain distribution must be an OptimizationDistribution"
            )
        for name, val in (
            ("min_value", self.min_value),
            ("max_value", self.max_value),
            ("step", self.step),
        ):
            if val is not None:
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise TypeError(f"OptimizationDomain {name} must be numeric")
                if not math.isfinite(val):
                    raise ValueError(f"OptimizationDomain {name} must be finite")
        if self.eligible:
            _validate_opt_bounds(self.min_value, self.max_value, self.step, self.scale)
            if self.distribution is OptimizationDistribution.NORMAL and (
                self.min_value is None or self.max_value is None
            ):
                raise ValueError(
                    "Normal optimization distribution requires finite "
                    "min_value and max_value"
                )


class WidgetKind(StrEnum):
    """Safe UI control representations."""

    NUMERIC_INPUT = "numeric_input"
    SLIDER = "slider"
    TEXT_INPUT = "text_input"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"


@dataclass(frozen=True, slots=True)
class PresentationHint:
    """Safe, bounded UI presentation hints."""

    widget: WidgetKind
    group: str = ""
    order: int = 0
    label: str = ""
    help_text: str = ""

    def __post_init__(self) -> None:
        """Validate presentation hints."""
        if not isinstance(self.widget, WidgetKind):
            raise TypeError("PresentationHint widget must be a WidgetKind")
        if not isinstance(self.group, str) or len(self.group) > MAX_STRING_LENGTH:
            raise ValueError("PresentationHint group must be a bounded string")
        if not isinstance(self.order, int):
            raise TypeError("PresentationHint order must be an integer")
        if not isinstance(self.label, str) or len(self.label) > MAX_STRING_LENGTH:
            raise ValueError("PresentationHint label must be a bounded string")
        if (
            not isinstance(self.help_text, str)
            or len(self.help_text) > MAX_STRING_LENGTH
        ):
            raise ValueError("PresentationHint help_text must be a bounded string")


def _validate_numeric_constraint(
    kind: ValueKind,
    constraint: NumericConstraint,
) -> None:
    """Validate numeric constraint properties."""
    if kind == ValueKind.INTEGER:
        for val in (constraint.min_value, constraint.max_value, constraint.step):
            if val is not None and not isinstance(val, int):
                raise TypeError("Integer constraints must use int values")


def _validate_param_constraint(
    kind: ValueKind,
    constraint: NumericConstraint | TextConstraint | EnumConstraint | None,
) -> None:
    """Validate constraint compatibility with declared parameter kind."""
    if constraint is None:
        return
    if kind in (ValueKind.INTEGER, ValueKind.NUMBER):
        if not isinstance(constraint, NumericConstraint):
            raise TypeError("Numeric kinds require NumericConstraint")
        _validate_numeric_constraint(kind, constraint)
    elif kind == ValueKind.TEXT:
        if not isinstance(constraint, TextConstraint):
            raise TypeError("Text kind requires TextConstraint")
    elif kind == ValueKind.ENUM:
        if not isinstance(constraint, EnumConstraint):
            raise TypeError("Enum kind requires EnumConstraint")
    else:
        raise ValueError(f"Constraints not supported for kind {kind}")


def _validate_param_default(
    kind: ValueKind,
    default: Value,
    constraint: NumericConstraint | TextConstraint | EnumConstraint | None,
) -> None:
    """Validate default parameter value against kind and constraint."""
    if default is None:
        return
    if constraint is not None:
        issues = constraint.validate(default)
        if issues:
            raise ValueError(
                f"Default value {default!r} violates constraint: {'; '.join(issues)}"
            )
    if kind == ValueKind.BOOLEAN and not isinstance(default, bool):
        raise TypeError("Boolean default must be bool")
    if kind == ValueKind.INTEGER and (
        not isinstance(default, int) or isinstance(default, bool)
    ):
        raise TypeError("Integer default must be int")
    if kind == ValueKind.NUMBER and (
        not isinstance(default, (int, float)) or isinstance(default, bool)
    ):
        raise TypeError("Number default must be int or float")


def _validate_param_optimization(
    kind: ValueKind,
    constraint: NumericConstraint | TextConstraint | EnumConstraint | None,
    optimization: OptimizationDomain | None,
) -> None:
    """Validate optimization domain compatibility with validity constraint."""
    if optimization is None:
        return
    if not isinstance(optimization, OptimizationDomain):
        raise TypeError("optimization must be an OptimizationDomain")
    if not optimization.eligible:
        return
    if kind not in (ValueKind.INTEGER, ValueKind.NUMBER):
        raise ValueError("Optimization domain is only supported for numeric kinds")
    if isinstance(constraint, NumericConstraint):
        if (
            optimization.min_value is not None
            and constraint.min_value is not None
            and optimization.min_value < constraint.min_value
        ):
            raise ValueError("Optimization min_value cannot exceed constraint minimum")
        if (
            optimization.max_value is not None
            and constraint.max_value is not None
            and optimization.max_value > constraint.max_value
        ):
            raise ValueError("Optimization max_value cannot exceed constraint maximum")


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """Self-describing declaration for one configurable parameter."""

    key: str
    kind: ValueKind
    label: str
    description: str = ""
    required: bool = True
    default: Value = None
    constraint: NumericConstraint | TextConstraint | EnumConstraint | None = None
    optimization: OptimizationDomain | None = None
    presentation: PresentationHint | None = None

    def __post_init__(self) -> None:
        """Validate parameter declaration consistency and bounds."""
        validate_identifier(self.key, "ParameterSpec key")
        if not isinstance(self.kind, ValueKind):
            raise TypeError("ParameterSpec kind must be a ValueKind")
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("ParameterSpec label must be a non-empty string")
        if not isinstance(self.description, str):
            raise TypeError("ParameterSpec description must be a string")
        if not isinstance(self.required, bool):
            raise TypeError("ParameterSpec required must be a bool")

        _validate_param_constraint(self.kind, self.constraint)

        if self.default is not None:
            frozen_default = freeze_value(self.default)
            object.__setattr__(self, "default", frozen_default)
            _validate_param_default(self.kind, self.default, self.constraint)

        _validate_param_optimization(self.kind, self.constraint, self.optimization)


@dataclass(frozen=True, slots=True)
class ParameterSchema:
    """Collection of parameter declarations with unique keys."""

    parameters: tuple[ParameterSpec, ...] = ()

    def __post_init__(self) -> None:
        """Validate parameter uniqueness."""
        if not isinstance(self.parameters, tuple):
            raise TypeError("ParameterSchema parameters must be a tuple")
        seen: set[str] = set()
        for p in self.parameters:
            if not isinstance(p, ParameterSpec):
                raise TypeError(
                    "ParameterSchema entries must be ParameterSpec instances"
                )
            if p.key in seen:
                raise ValueError(f"Duplicate parameter key in schema: {p.key!r}")
            seen.add(p.key)

    def get(self, key: str) -> ParameterSpec | None:
        """Find a parameter spec by key."""
        for p in self.parameters:
            if p.key == key:
                return p
        return None

    def keys(self) -> tuple[str, ...]:
        """Return tuple of parameter keys."""
        return tuple(p.key for p in self.parameters)

    def validate_bindings(self, values: FrozenObject) -> ParameterBindingResult:
        """Validate provided parameter values against declared schema.

        Args:
            values: Parameter values mapping.

        Returns:
            ParameterBindingResult with issues and normalized values.
        """
        if not isinstance(values, FrozenObject):
            raise TypeError("Parameter values must be a FrozenObject")
        issues: list[ValidationIssue] = [
            ValidationIssue(
                path=key,
                code="UNKNOWN_PARAMETER",
                message=f"Parameter {key!r} is not declared in schema",
            )
            for key in values
            if self.get(key) is None
        ]

        normalized: dict[str, Value] = {}
        for spec in self.parameters:
            if spec.key in values:
                val = values[spec.key]
                if spec.constraint is not None:
                    issues.extend(
                        ValidationIssue(
                            path=spec.key,
                            code="CONSTRAINT_VIOLATION",
                            message=err,
                        )
                        for err in spec.constraint.validate(val)
                    )
                elif spec.kind == ValueKind.BOOLEAN and not isinstance(val, bool):
                    issues.append(
                        ValidationIssue(
                            path=spec.key,
                            code="TYPE_MISMATCH",
                            message=f"Expected boolean, got {type(val).__name__}",
                        )
                    )
                normalized[spec.key] = val
            elif spec.default is not None:
                normalized[spec.key] = spec.default
            elif spec.required:
                issues.append(
                    ValidationIssue(
                        path=spec.key,
                        code="MISSING_REQUIRED",
                        message=f"Required parameter {spec.key!r} is missing",
                    )
                )

        return ParameterBindingResult(
            is_valid=len(issues) == 0,
            issues=tuple(issues),
            values=FrozenObject.from_mapping(normalized),
        )


@dataclass(frozen=True, slots=True)
class PortSpec:
    """Self-describing declaration for an input or output port."""

    key: str
    kind: ValueKind
    unit: Unit = Unit.NONE
    alignment: Alignment = Alignment.NONE
    label: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate port declaration."""
        validate_identifier(self.key, "PortSpec key")
        if not isinstance(self.kind, ValueKind):
            raise TypeError("PortSpec kind must be a ValueKind")
        if not isinstance(self.unit, Unit):
            raise TypeError("PortSpec unit must be a Unit")
        if not isinstance(self.alignment, Alignment):
            raise TypeError("PortSpec alignment must be an Alignment")
        if not isinstance(self.label, str):
            raise TypeError("PortSpec label must be a string")
        if not isinstance(self.description, str):
            raise TypeError("PortSpec description must be a string")


@dataclass(frozen=True, slots=True)
class NumericalPolicy:
    """Numerical precision and missing data behavior specification."""

    tolerance: float = 1e-9
    nan_policy: str = "reject"
    missing_policy: str = "propagate"

    def __post_init__(self) -> None:
        """Validate numerical policy values."""
        if not isinstance(self.tolerance, (int, float)) or self.tolerance <= 0:
            raise ValueError("tolerance must be a positive float")
        if self.nan_policy not in ("reject", "propagate"):
            raise ValueError(f"Invalid nan_policy: {self.nan_policy}")
        if self.missing_policy not in ("propagate", "reset", "interpolate"):
            raise ValueError(f"Invalid missing_policy: {self.missing_policy}")


class ValidationSeverity(StrEnum):
    """Validation issue importance level."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Describe one schema or graph validation issue."""

    path: str
    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR

    def __post_init__(self) -> None:
        """Validate issue fields."""
        if not isinstance(self.path, str):
            raise TypeError("ValidationIssue path must be a string")
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("ValidationIssue code must be a non-empty string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("ValidationIssue message must be a non-empty string")
        if not isinstance(self.severity, ValidationSeverity):
            raise TypeError("ValidationIssue severity must be a ValidationSeverity")


@dataclass(frozen=True, slots=True)
class ParameterBindingResult:
    """Result of validating and normalizing parameter bindings."""

    is_valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    values: FrozenObject = EMPTY_FROZEN_OBJECT

    def __post_init__(self) -> None:
        """Validate binding result consistency."""
        if not isinstance(self.is_valid, bool):
            raise TypeError("is_valid must be a bool")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")
        if not isinstance(self.values, FrozenObject):
            raise TypeError("values must be a FrozenObject")
