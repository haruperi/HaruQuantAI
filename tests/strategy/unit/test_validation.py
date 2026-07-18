"""Strategy reference and configuration validation tests."""

# ruff: noqa: PT018

from pathlib import Path

import pytest
from app.services.strategy import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyRef,
    register_strategy_version,
    validate_strategy_config,
    validate_strategy_ref,
)
from app.utils import logger
from pydantic import ValidationError

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import COR, REQ, make_auth, make_policy, make_ref


def test_version_constraint_resolves_exactly_one(tmp_path: Path) -> None:
    """Verify a constraint must resolve one approved immutable version."""
    logger.debug("Testing Strategy version resolution")
    with storage_context(tmp_path):
        register_strategy_version(make_registration(), make_auth(), make_policy())
        outcome = validate_strategy_ref(
            StrategyRef(
                strategy_id="mean-reversion",
                exact_version="1.0.0",
                environment=StrategyEnvironment.RESEARCH,
                request_id=REQ,
                correlation_id=COR,
            ),
            make_policy(),
        )
    assert outcome.status == "success"


def test_config_rejects_executable_injection() -> None:
    """Verify executable-looking strings fail closed before schema use."""
    logger.debug("Testing Strategy config injection rejection")
    with pytest.raises(ValidationError):
        StrategyConfig(
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            config_schema_version="v1",
            parameters={"period": 5, "mode": "exec(payload)"},
            request_id=REQ,
        )


def test_config_applies_explicit_schema_default() -> None:
    """Verify only manifest-declared defaults are applied."""
    logger.debug("Testing explicit Strategy config default")
    config = StrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"period": 5},
        request_id=REQ,
    )
    outcome = validate_strategy_config(make_ref(), config)
    assert (
        outcome.data is not None
        and outcome.data.normalized_parameters["mode"] == "strict"
    )
