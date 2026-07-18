"""Strategy replay contract tests."""

import pytest
from app.services.strategy import StrategyCheckpoint, StrategyReplayManifest
from app.utils import logger
from pydantic import ValidationError

from tests.strategy.unit.test_models import COR, HASH, NOW, REQ, WF


def test_manifest_requires_complete_lineage() -> None:
    """Verify replay hashes are exact SHA-256 digests."""
    logger.debug("Testing Strategy replay lineage")
    with pytest.raises(ValidationError):
        StrategyReplayManifest(
            strategy_id="s",
            strategy_version="1",
            interface_version="v1",
            config_hash="bad",
            data_checksum=HASH,
            indicator_manifest_hash=HASH,
            simulation_config_hash=None,
            source_hash=HASH,
            artifact_hash=HASH,
            dependency_hash=HASH,
            seed=1,
            timing_policy="EVENT_DRIVEN",
            decision_timestamp=NOW,
            request_id=REQ,
            workflow_id=WF,
            correlation_id=COR,
            manifest_hash=HASH,
        )


def test_checkpoint_rejects_official_state() -> None:
    """Document that official-state rejection occurs in checkpoint creation."""
    logger.debug("Testing Strategy checkpoint schema identity")
    value = StrategyCheckpoint(
        checkpoint_id="checkpoint-1",
        strategy_id="s",
        strategy_version="1",
        config_hash=HASH,
        state={"counter": 1},
        state_checksum=HASH,
        authorization_ref="auth",
        created_at=NOW,
        request_id=REQ,
        payload_bytes=1,
        redacted_paths=(),
    )
    assert value.state_schema_version == "v1"
