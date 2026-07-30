"""WF-STR-001 registry resolution and configuration integration."""

from pathlib import Path

from app.services.strategy import (
    create_strategy_config,
    create_strategy_ref,
    get_strategy_environment,
    register_strategy_version,
    validate_strategy_config,
    validate_strategy_ref,
)
from app.utils import get_logger

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import COR, REQ, make_auth, make_policy

logger = get_logger(__name__)


def test_registry_validation_workflow(tmp_path: Path) -> None:
    """Register, resolve, and validate one declarative configuration."""
    logger.debug("Testing WF-STR-001 registry validation")
    ref = create_strategy_ref(
        strategy_id="mean-reversion",
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=REQ,
        correlation_id=COR,
    )
    with storage_context(tmp_path):
        assert (
            register_strategy_version(
                make_registration(), make_auth(), make_policy()
            ).status
            == "success"
        )
        resolved = validate_strategy_ref(ref, make_policy())
    assert resolved.data is not None
    config = create_strategy_config(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"period": 5},
        request_id=REQ,
    )
    assert validate_strategy_config(resolved.data, config).status == "success"
