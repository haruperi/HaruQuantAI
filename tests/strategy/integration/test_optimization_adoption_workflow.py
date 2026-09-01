"""WF-STR-011 Strategy-owned approved parameter adoption workflow."""

from pathlib import Path

from app.composition.logging import get_logger
from app.services.strategy import (
    adopt_approved_optimization_parameters,
    register_strategy_version,
)

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import make_auth, make_policy
from tests.strategy.unit.test_optimization_adoption import (
    make_optimization_handoff,
    make_optimization_update,
)

logger = get_logger(__name__)


def test_compatible_handoff_creates_real_immutable_strategy_config(
    tmp_path: Path,
) -> None:
    """Persist the selected candidate only through Strategy's mutation rules."""
    logger.debug("Testing full approved Optimization handoff adoption")
    auth = make_auth().model_copy(update={"scopes": ("approval-optimization",)})
    with storage_context(tmp_path):
        registration = register_strategy_version(
            make_registration(),
            auth,
            make_policy(),
        )
        outcome = adopt_approved_optimization_parameters(
            make_optimization_update(),
            auth,
            make_optimization_handoff(),
        )
    assert registration.data is not None
    assert registration.data.status == "ACCEPTED"
    assert outcome.data is not None
    assert outcome.data.status == "ACCEPTED"
    assert outcome.data.validated_config is not None
    assert outcome.data.validated_config.normalized_parameters == {
        "mode": "strict",
        "period": 7,
    }
    assert outcome.data.record_hash == outcome.data.validated_config.config_hash
    assert outcome.metadata.modifies_database is True
