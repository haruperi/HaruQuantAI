"""Focused edge coverage for Optimization's public and internal boundaries."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.optimization import (
    apply_execution_cost_stress,
    create_optimization_value,
    dump_optimization_value,
    evaluate_constraints,
    get_optimization_value_field,
    is_optimization_value,
    iter_grid_candidates,
    load_search_checkpoint,
    run_monte_carlo,
    run_parametric_simulation,
    save_search_checkpoint,
    validate_parameter_space,
)
from app.services.optimization.errors import OptimizationError
from app.services.optimization.parameters.constraints import _evaluate
from app.services.optimization.parameters.contracts import (
    ParameterRange,
    ParameterSpace,
)
from app.services.optimization.robustness.barrier import FirstPassageReport
from app.services.optimization.robustness.contracts import (
    ExecutionStressRequest,
    MonteCarloRequest,
    MonteCarloResult,
)
from app.services.optimization.state.contracts import (
    OptimizationCheckpoint,
    OptimizationPersistenceReceipt,
    OptimizationStateStore,
)
from pydantic import ValidationError

NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _checkpoint(**updates: object) -> OptimizationCheckpoint:
    """Build one valid checkpoint with optional replacements."""
    values: dict[str, object] = {
        "search_id": "search-one",
        "reproducibility_hash": "a" * 64,
        "completed_candidate_position": 1,
        "created_at": NOW,
    }
    values.update(updates)
    return OptimizationCheckpoint.model_validate(values)


def _receipt(**updates: object) -> OptimizationPersistenceReceipt:
    """Build one valid durable receipt with optional replacements."""
    values: dict[str, object] = {
        "search_id": "search-one",
        "reproducibility_hash": "a" * 64,
        "stored_at": NOW,
        "durable": True,
    }
    values.update(updates)
    return OptimizationPersistenceReceipt.model_validate(values)


def test_function_only_value_boundary_covers_success_and_rejection() -> None:
    """Opaque construction, inspection, predicates, and dumping fail closed."""
    value = create_optimization_value(
        "ParameterRange", name="period", kind="fixed", fixed_value=14
    )
    assert get_optimization_value_field(value, "name") == "period"
    assert dump_optimization_value(value)["fixed_value"] == 14
    assert is_optimization_value(value)
    assert is_optimization_value(value, "ParameterRange")
    assert not is_optimization_value(value, "Missing")
    assert not is_optimization_value(object())

    report = FirstPassageReport(
        "v1",
        "static",
        10,
        1,
        Decimal("0.1"),
        Decimal("0.2"),
        Decimal("0.3"),
        Decimal("0.4"),
        Decimal(2),
    )
    assert dump_optimization_value(report)["median_termination_day"] == 2
    assert is_optimization_value(report)

    with pytest.raises(ValueError, match="Unknown"):
        create_optimization_value("Missing")
    with pytest.raises(ValueError, match="registered"):
        dump_optimization_value(object())
    with pytest.raises(ValueError, match="requested"):
        get_optimization_value_field(value, "_private")
    with pytest.raises(ValueError, match="requested"):
        get_optimization_value_field(value, "missing")


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"name": "_bad", "kind": "boolean"}, "identifier"),
        (
            {
                "name": "x",
                "kind": "integer",
                "minimum": Decimal(0),
                "maximum": Decimal(1),
            },
            "require",
        ),
        (
            {
                "name": "x",
                "kind": "integer",
                "minimum": Decimal(2),
                "maximum": Decimal(1),
                "step": Decimal(1),
            },
            "bounds",
        ),
        (
            {
                "name": "x",
                "kind": "integer",
                "minimum": Decimal(0),
                "maximum": Decimal(1),
                "step": Decimal("0.5"),
            },
            "integral",
        ),
        (
            {"name": "x", "kind": "categorical", "choices": ()},
            "non-empty",
        ),
        (
            {"name": "x", "kind": "boolean", "choices": (True,)},
            "categorical",
        ),
        ({"name": "x", "kind": "fixed"}, "fixed_value"),
        (
            {"name": "x", "kind": "boolean", "fixed_value": True},
            "fixed parameters",
        ),
        (
            {"name": "x", "kind": "boolean", "active_when": " x"},
            "trimmed",
        ),
    ],
)
def test_parameter_range_rejects_malformed_definitions(
    values: dict[str, object], message: str
) -> None:
    """Every parameter-kind invariant rejects contradictory definitions."""
    with pytest.raises(ValidationError, match=message):
        ParameterRange.model_validate(values)


def test_parameter_space_and_expression_edges_are_enforced() -> None:
    """Space bounds and the complete safe expression grammar are exercised."""
    fixed = ParameterRange(name="x", kind="fixed", fixed_value=2)
    with pytest.raises(ValidationError, match="must not be empty"):
        ParameterSpace(parameters=())
    with pytest.raises(ValidationError, match="unique"):
        ParameterSpace(parameters=(fixed, fixed))
    with pytest.raises(ValidationError, match="trimmed"):
        ParameterSpace(parameters=(fixed,), constraints=(" ",))

    space = ParameterSpace(parameters=(fixed,), constraints=("x == 2",))
    with pytest.raises(ValueError, match="positive"):
        validate_parameter_space(space, max_expansion=0, max_constraints=1)
    too_many = ParameterSpace(parameters=(fixed,), constraints=("x == 2", "x > 0"))
    with pytest.raises(ValueError, match="count"):
        validate_parameter_space(too_many, max_expansion=2, max_constraints=1)
    with pytest.raises(ValueError, match="syntax"):
        evaluate_constraints({"x": 2}, ("x ==",))
    with pytest.raises(ValueError, match="unknown"):
        evaluate_constraints({"x": 2}, ("y == 2",))
    with pytest.raises(ValueError, match="unsupported"):
        evaluate_constraints({"x": 2}, ("x == 1.5",))
    with pytest.raises(ValueError, match="missing"):
        _evaluate(ast.Name(id="x"), {})
    with pytest.raises(ValueError, match="arithmetic"):
        evaluate_constraints({"x": "a"}, ("x / 2 == 1",))
    with pytest.raises(ValueError, match="comparison"):
        evaluate_constraints({"x": object()}, ("x < 2",))
    assert evaluate_constraints(
        {"x": 2},
        (
            "not False",
            "-x == -2",
            "+x == 2",
            "x + 1 == 3",
            "x in [1, 2]",
            "x not in (3, 4)",
            "x == 2 and (x < 3 or x > 10)",
        ),
    )


def test_grid_generation_exercises_kinds_and_cap_failures() -> None:
    """Grid generation covers categorical, Boolean, fixed, and rejection paths."""
    space = ParameterSpace(
        parameters=(
            ParameterRange(name="category", kind="categorical", choices=("a", "b")),
            ParameterRange(name="enabled", kind="boolean"),
            ParameterRange(name="period", kind="fixed", fixed_value=2),
        ),
        constraints=("category == 'a'",),
    )
    generated = tuple(
        iter_grid_candidates(
            space, max_candidates=2, max_expansion=4, max_constraints=2
        )
    )
    assert len(generated) == 2
    with pytest.raises(ValueError, match="positive"):
        tuple(
            iter_grid_candidates(
                space, max_candidates=0, max_expansion=4, max_constraints=2
            )
        )
    with pytest.raises(ValueError, match="candidate count"):
        tuple(
            iter_grid_candidates(
                space, max_candidates=1, max_expansion=4, max_constraints=2
            )
        )
    impossible = ParameterSpace(
        parameters=(ParameterRange(name="x", kind="fixed", fixed_value=1),),
        constraints=("x == 2",),
    )
    with pytest.raises(ValueError, match="no valid"):
        tuple(
            iter_grid_candidates(
                impossible, max_candidates=1, max_expansion=1, max_constraints=1
            )
        )


def test_robustness_contract_and_calculation_edges() -> None:
    """Robustness contracts and calculations reject malformed bounds."""
    with pytest.raises(ValidationError):
        MonteCarloRequest(
            outcomes=(Decimal(1),),
            initial_balance=Decimal(0),
            method="resample_returns",
            simulations=1,
            seed=1,
        )
    with pytest.raises(ValidationError):
        ExecutionStressRequest(kind="skip_trade", value=Decimal("0.1"))
    with pytest.raises(ValueError, match="cap"):
        run_monte_carlo(
            MonteCarloRequest(
                outcomes=(Decimal(1),),
                initial_balance=Decimal(100),
                method="resample_returns",
                simulations=2,
                seed=1,
            ),
            max_simulations=1,
        )
    with pytest.raises(ValueError, match="assumptions"):
        run_parametric_simulation(
            win_rate=Decimal(2),
            reward_risk=Decimal(1),
            risk_per_trade=Decimal("0.1"),
            trade_count=1,
            simulations=1,
            initial_balance=Decimal(100),
            seed=1,
            max_simulations=1,
        )
    with pytest.raises(ValueError, match="empty"):
        apply_execution_cost_stress((), ExecutionStressRequest(kind="spread", value=1))
    with pytest.raises(ValueError, match="Decimal"):
        apply_execution_cost_stress(
            ({"pnl": 1},), ExecutionStressRequest(kind="spread", value=1)
        )
    skipped = apply_execution_cost_stress(
        ({"pnl": Decimal(1)},),
        ExecutionStressRequest(kind="skip_trade", value=Decimal(1), seed=1),
    )
    assert skipped[0]["pnl"] == 0


@pytest.mark.parametrize(
    "updates",
    [
        {"outcomes": (Decimal("NaN"),)},
        {"simulations": 0},
        {"method": "block_bootstrap"},
        {"method": "resample_returns", "block_size": 1},
        {"ruin_threshold": Decimal(100)},
        {"confidence_level": 1.0},
    ],
)
def test_monte_carlo_request_rejects_each_invalid_policy(
    updates: dict[str, object],
) -> None:
    """Every method-specific Monte Carlo policy is independently enforced."""
    values: dict[str, object] = {
        "outcomes": (Decimal(1), Decimal(-1)),
        "initial_balance": Decimal(100),
        "method": "resample_returns",
        "simulations": 2,
        "seed": 1,
    }
    values.update(updates)
    with pytest.raises(ValidationError):
        MonteCarloRequest.model_validate(values)


@pytest.mark.parametrize(
    "updates",
    [
        {"final_equity": (Decimal("NaN"),)},
        {"max_drawdowns": (Decimal(-1),)},
        {"sub_seed_policy": " "},
        {"ruin_probability": 2.0},
        {"percentiles": {" ": Decimal(1)}},
    ],
)
def test_monte_carlo_result_rejects_invalid_evidence(
    updates: dict[str, object],
) -> None:
    """Every result-distribution invariant rejects contradictory evidence."""
    values: dict[str, object] = {
        "method": "resample_returns",
        "simulations": 1,
        "seed": 1,
        "sub_seed_policy": "v1",
        "final_equity": (Decimal(100),),
        "max_drawdowns": (Decimal(0),),
        "percentiles": {},
        "ruin_probability": None,
        "warnings": (),
    }
    values.update(updates)
    with pytest.raises(ValidationError):
        MonteCarloResult.model_validate(values)


@pytest.mark.parametrize(
    "values",
    [
        {"kind": "unknown", "value": Decimal(1)},
        {"kind": "spread", "value": Decimal(-1)},
        {"kind": "skip_trade", "value": Decimal(2), "seed": 1},
        {"kind": "spread", "value": Decimal(1), "seed": 1},
    ],
)
def test_execution_stress_request_rejects_invalid_policy(
    values: dict[str, object],
) -> None:
    """Stress catalog, amount, probability, and seed rules fail closed."""
    with pytest.raises(ValidationError):
        ExecutionStressRequest.model_validate(values)


class _Store:
    """Configurable store double for state-boundary failure verification."""

    def __init__(self, *, fail: bool = False, receipt: object | None = None) -> None:
        self.fail = fail
        self.receipt = receipt

    def save_checkpoint(self, checkpoint: object) -> object:
        """Return configured receipt or raise."""
        if self.fail:
            raise RuntimeError("write")
        return self.receipt or _receipt(
            search_id=checkpoint.search_id,
            reproducibility_hash=checkpoint.reproducibility_hash,
        )

    def load_checkpoint(self, search_id: str) -> object | None:
        """Return configured checkpoint or raise."""
        del search_id
        if self.fail:
            raise RuntimeError("read")
        return self.receipt


def test_state_contract_and_store_failures_are_controlled() -> None:
    """State timestamps, identities, receipts, and injected failures fail closed."""
    for updates in (
        {"schema_version": "v2"},
        {"search_id": "bad"},
        {"reproducibility_hash": "bad"},
        {"completed_candidate_position": -1},
        {"created_at": NOW.replace(tzinfo=None)},
        {"evidence_references": (" ",)},
    ):
        with pytest.raises(ValidationError):
            _checkpoint(**updates)
    for updates in (
        {"schema_version": "v2"},
        {"search_id": "bad"},
        {"reproducibility_hash": "bad"},
        {"stored_at": NOW.replace(tzinfo=None)},
        {"durable": False},
    ):
        with pytest.raises(ValidationError):
            _receipt(**updates)

    checkpoint = _checkpoint()
    with pytest.raises(OptimizationError, match="CHECKPOINT_WRITE_FAILED"):
        save_search_checkpoint(checkpoint, _Store(fail=True))
    with pytest.raises(OptimizationError, match="RECEIPT_IDENTITY_MISMATCH"):
        save_search_checkpoint(
            checkpoint,
            _Store(receipt=_receipt(search_id="search-other")),
        )
    with pytest.raises(OptimizationError, match="CHECKPOINT_READ_FAILED"):
        load_search_checkpoint(
            search_id="search-one",
            reproducibility_hash="a" * 64,
            store=_Store(fail=True),
        )
    assert (
        load_search_checkpoint(
            search_id="search-one",
            reproducibility_hash="a" * 64,
            store=_Store(),
        )
        is None
    )
    with pytest.raises(OptimizationError, match="CHECKPOINT_IDENTITY_MISMATCH"):
        load_search_checkpoint(
            search_id="search-one",
            reproducibility_hash="a" * 64,
            store=_Store(receipt=_checkpoint(search_id="search-other")),
        )

    protocol = object.__new__(OptimizationStateStore)
    with pytest.raises(NotImplementedError):
        protocol.save_checkpoint(checkpoint)
    with pytest.raises(NotImplementedError):
        protocol.load_checkpoint("search-one")
    with pytest.raises(NotImplementedError):
        protocol.save_result(SimpleNamespace(search_id="search-one"), ())
