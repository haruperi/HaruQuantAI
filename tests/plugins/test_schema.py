"""Unit tests for app.plugins.schema: values, constraints, schemas, and presentation hints."""

from typing import Any, cast

import pytest
from app.plugins.schema import (
    INT_MAX,
    INT_MIN,
    MAX_COLLECTION_SIZE,
    MAX_VALUE_DEPTH,
    Alignment,
    EnumChoice,
    EnumConstraint,
    FrozenArray,
    FrozenObject,
    MissingValue,
    NumericalPolicy,
    NumericConstraint,
    OptimizationDomain,
    OptimizationScale,
    ParameterSchema,
    ParameterSpec,
    PortSpec,
    PresentationHint,
    TextConstraint,
    Unit,
    ValueKind,
    WidgetKind,
    freeze_value,
    validate_identifier,
)


def test_validate_identifier_valid() -> None:
    assert validate_identifier("period") == "period"
    assert validate_identifier("fast_period_1") == "fast_period_1"


def test_validate_identifier_invalid() -> None:
    with pytest.raises(ValueError, match="non-empty lowercase"):
        validate_identifier("Period")
    with pytest.raises(ValueError, match="non-empty lowercase"):
        validate_identifier("123period")
    with pytest.raises(ValueError, match="non-empty lowercase"):
        validate_identifier("period-name")
    with pytest.raises(ValueError, match="non-empty lowercase"):
        validate_identifier("")
    with pytest.raises(TypeError):
        validate_identifier(123)  # type: ignore[arg-type]


def test_missing_value_properties() -> None:
    m1 = MissingValue(reason="warmup gap")
    assert m1.reason == "warmup gap"
    assert m1 != cast("object", None)
    assert m1 != cast("object", "")
    assert isinstance(m1, MissingValue)
    with pytest.raises(TypeError):
        MissingValue(reason=123)  # type: ignore[arg-type]


def test_frozen_array_immutability_and_bounds() -> None:
    arr = FrozenArray((1, 2, "three"))
    assert len(arr) == 3
    assert arr[0] == 1
    assert list(arr) == [1, 2, "three"]
    assert "FrozenArray" in repr(arr)

    with pytest.raises(TypeError):
        arr[0] = 10  # type: ignore[index]

    with pytest.raises(TypeError):
        FrozenArray([1, 2])  # type: ignore[arg-type]

    oversized = tuple(range(MAX_COLLECTION_SIZE + 1))
    with pytest.raises(ValueError, match="exceeds limit"):
        FrozenArray(oversized)


def test_frozen_object_immutability_sorting_and_uniqueness() -> None:
    obj = FrozenObject.from_mapping({"b": 2, "a": 1})
    assert list(obj.keys()) == ["a", "b"]
    assert obj["a"] == 1
    assert obj["b"] == 2
    assert obj.get("c", 99) == 99
    assert "a" in obj
    assert len(obj) == 2

    with pytest.raises(TypeError):
        obj["a"] = 10  # type: ignore[index]

    # Duplicate keys in raw pairs rejected
    with pytest.raises(ValueError, match="Duplicate key"):
        FrozenObject((("a", 1), ("a", 2)))

    # Unsorted pairs rejected
    with pytest.raises(ValueError, match="must be sorted"):
        FrozenObject((("b", 1), ("a", 2)))

    # Non-string key rejected
    with pytest.raises(TypeError, match="must be strings"):
        FrozenObject(((123, 1),))  # type: ignore[arg-type]


def test_freeze_value_recursion_and_primitives() -> None:
    raw = {
        "int_val": 42,
        "float_val": 3.14,
        "bool_val": True,
        "str_val": "hello",
        "missing_val": MissingValue("gap"),
        "list_val": [1, 2, {"nested": "value"}],
    }
    frozen = freeze_value(raw)
    assert isinstance(frozen, FrozenObject)
    assert isinstance(frozen["list_val"], FrozenArray)
    nested_obj = frozen["list_val"][2]
    assert isinstance(nested_obj, FrozenObject)
    assert nested_obj["nested"] == "value"


def test_freeze_value_rejections() -> None:
    with pytest.raises(ValueError, match="must be finite"):
        freeze_value(float("nan"))
    with pytest.raises(ValueError, match="must be finite"):
        freeze_value(float("inf"))
    with pytest.raises(ValueError, match="outside safe bounds"):
        freeze_value(INT_MAX + 1)
    with pytest.raises(ValueError, match="outside safe bounds"):
        freeze_value(INT_MIN - 1)
    with pytest.raises(TypeError, match="Unsupported leaf value"):
        freeze_value(object())

    # Nesting depth exceeded
    deep: Any = "leaf"
    for _ in range(MAX_VALUE_DEPTH + 2):
        deep = {"layer": deep}
    with pytest.raises(ValueError, match="nesting depth exceeds limit"):
        freeze_value(deep)


def test_numeric_constraint_validation() -> None:
    c = NumericConstraint(min_value=2, max_value=100, step=1, allow_negative=False)
    assert c.validate(14) == []
    assert len(c.validate(1)) == 1  # Below min
    assert len(c.validate(101)) == 1  # Above max
    assert len(c.validate(-5)) >= 1  # Negative not allowed
    assert len(c.validate("not a number")) == 1

    with pytest.raises(ValueError, match=r"min_value.*> max_value"):
        NumericConstraint(min_value=100, max_value=2)
    with pytest.raises(ValueError, match="step must be > 0"):
        NumericConstraint(step=0)
    with pytest.raises(ValueError, match="cannot be negative"):
        NumericConstraint(min_value=-1, allow_negative=False)


def test_text_constraint_validation() -> None:
    c = TextConstraint(min_length=2, max_length=10, pattern=r"^[a-z]+$")
    assert c.validate("hello") == []
    assert len(c.validate("a")) == 1  # Too short
    assert len(c.validate("verylongtextvalue")) == 1  # Too long
    assert len(c.validate("Hello123")) == 1  # Regex mismatch

    with pytest.raises(ValueError, match="max_length must be between"):
        TextConstraint(min_length=10, max_length=5)
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        TextConstraint(pattern="[invalid")


def test_enum_constraint_validation() -> None:
    choices = (
        EnumChoice(value="open", label="Open Price"),
        EnumChoice(value="close", label="Close Price"),
    )
    c = EnumConstraint(choices=choices)
    assert c.validate("open") == []
    assert c.validate("close") == []
    assert len(c.validate("high")) == 1

    with pytest.raises(ValueError, match="Duplicate enum choice"):
        EnumConstraint(
            choices=(
                EnumChoice(value="open", label="Open 1"),
                EnumChoice(value="open", label="Open 2"),
            )
        )


def test_optimization_domain_validation() -> None:
    opt = OptimizationDomain(
        eligible=True,
        min_value=2,
        max_value=100,
        step=1,
        scale=OptimizationScale.LINEAR,
    )
    assert opt.eligible is True

    with pytest.raises(ValueError, match=r"min_value.*> max_value"):
        OptimizationDomain(eligible=True, min_value=10, max_value=5)
    with pytest.raises(ValueError, match="step must be > 0"):
        OptimizationDomain(eligible=True, step=-1)
    with pytest.raises(ValueError, match="Logarithmic scale requires min_value > 0"):
        OptimizationDomain(
            eligible=True, min_value=0, scale=OptimizationScale.LOGARITHMIC
        )


def test_parameter_spec_and_schema_bindings() -> None:
    period_spec = ParameterSpec(
        key="period",
        kind=ValueKind.INTEGER,
        label="Period",
        default=14,
        constraint=NumericConstraint(min_value=2, max_value=1000, step=1),
        optimization=OptimizationDomain(
            eligible=True, min_value=2, max_value=100, step=1
        ),
        presentation=PresentationHint(widget=WidgetKind.NUMERIC_INPUT, label="Period"),
    )
    schema = ParameterSchema((period_spec,))
    assert schema.get("period") == period_spec
    assert schema.keys() == ("period",)

    # Validate defaults applied when missing
    res = schema.validate_bindings(FrozenObject())
    assert res.is_valid is True
    assert res.values["period"] == 14

    # Validate provided valid value
    res2 = schema.validate_bindings(FrozenObject.from_mapping({"period": 20}))
    assert res2.is_valid is True
    assert res2.values["period"] == 20

    # Validate invalid value caught
    res3 = schema.validate_bindings(FrozenObject.from_mapping({"period": 1}))
    assert res3.is_valid is False
    assert len(res3.issues) == 1
    assert res3.issues[0].code == "CONSTRAINT_VIOLATION"

    # Validate unknown parameter caught
    res4 = schema.validate_bindings(FrozenObject.from_mapping({"unknown_param": 10}))
    assert res4.is_valid is False
    assert any(i.code == "UNKNOWN_PARAMETER" for i in res4.issues)


def test_parameter_spec_rejections() -> None:
    # Incompatible constraint with kind
    with pytest.raises(TypeError, match="Numeric kinds require NumericConstraint"):
        ParameterSpec(
            key="period",
            kind=ValueKind.INTEGER,
            label="Period",
            constraint=TextConstraint(),
        )

    # Default violates constraint
    with pytest.raises(ValueError, match="violates constraint"):
        ParameterSpec(
            key="period",
            kind=ValueKind.INTEGER,
            label="Period",
            default=1,
            constraint=NumericConstraint(min_value=2, max_value=100),
        )

    # Optimization domain exceeds validity constraint
    with pytest.raises(
        ValueError, match="Optimization min_value cannot exceed constraint minimum"
    ):
        ParameterSpec(
            key="period",
            kind=ValueKind.INTEGER,
            label="Period",
            constraint=NumericConstraint(min_value=5, max_value=100),
            optimization=OptimizationDomain(eligible=True, min_value=2, max_value=50),
        )


def test_port_spec_and_numerical_policy() -> None:
    port = PortSpec(
        key="values",
        kind=ValueKind.ALIGNED_SERIES,
        unit=Unit.NONE,
        alignment=Alignment.INDEX,
        label="Input Values",
    )
    assert port.key == "values"
    assert port.kind == ValueKind.ALIGNED_SERIES

    pol = NumericalPolicy(
        tolerance=1e-8, nan_policy="reject", missing_policy="propagate"
    )
    assert pol.tolerance == 1e-8
    assert pol.nan_policy == "reject"
    assert pol.missing_policy == "propagate"

    with pytest.raises(ValueError, match="tolerance must be a positive float"):
        NumericalPolicy(tolerance=0)
    with pytest.raises(ValueError, match="Invalid nan_policy"):
        NumericalPolicy(nan_policy="ignore")


def test_freeze_value_total_element_limit() -> None:
    from app.plugins.schema import MAX_TOTAL_ELEMENTS

    huge = list(range(MAX_TOTAL_ELEMENTS + 1))
    with pytest.raises(ValueError, match="Total frozen element count"):
        freeze_value(huge)

    # nested composition is also bounded across the whole tree
    deep_total = {"a": list(range(MAX_TOTAL_ELEMENTS + 1))}
    with pytest.raises(ValueError, match="Total frozen element count"):
        freeze_value(deep_total)


def test_optimization_distribution_validation() -> None:
    from app.plugins.schema import (
        OptimizationDistribution,
        OptimizationDomain,
    )

    # default is uniform
    domain = OptimizationDomain(min_value=2, max_value=100)
    assert domain.distribution is OptimizationDistribution.UNIFORM

    # normal distribution requires finite bounds
    normal_ok = OptimizationDomain(
        min_value=2, max_value=100, distribution=OptimizationDistribution.NORMAL
    )
    assert normal_ok.distribution is OptimizationDistribution.NORMAL
    with pytest.raises(ValueError, match="Normal optimization distribution"):
        OptimizationDomain(distribution=OptimizationDistribution.NORMAL)

    with pytest.raises(TypeError, match="OptimizationDistribution"):
        OptimizationDomain(distribution="uniform")  # type: ignore[arg-type]
