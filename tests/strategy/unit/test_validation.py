"""Strategy reference and configuration validation tests."""

# ruff: noqa: PT018
import pytest
from app.composition.logging import get_logger
from app.services.strategy import (
    validate_strategy_config,
    validate_strategy_ref,
)
from app.services.strategy.contracts import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyRef,
)
from pydantic import ValidationError

from tests.strategy.unit.test_models import (
    COR,
    HASH_B,
    REQ,
    make_manifest,
    make_policy,
    make_ref,
)

logger = get_logger(__name__)


def test_version_constraint_resolves_exactly_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify a constraint must resolve one approved immutable version."""
    logger.debug("Testing Strategy version resolution")
    manifest = make_manifest()
    policy = make_policy()
    row = {
        "manifest_json": manifest.model_dump_json(),
        "lifecycle_status": "APPROVED",
        "policy_json": policy.model_dump_json(),
        "record_hash": HASH_B,
        "request_id": REQ,
        "correlation_id": COR,
    }
    monkeypatch.setattr(
        "app.services.strategy.registry.resolution.read_strategy_versions",
        lambda *_args, **_kwargs: (row,),
    )
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
