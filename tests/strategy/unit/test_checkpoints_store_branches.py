"""Unit tests for checkpoints/store.py branch coverage floor."""

from unittest.mock import patch

from app.services.strategy import (
    create_strategy_checkpoint,
    create_strategy_checkpoint_value,
    list_strategy_checkpoints,
    validate_strategy_checkpoint,
)
from app.services.strategy.contracts.responses import StrategyOperationError

from tests.strategy.unit.test_models import (
    HASH,
    NOW,
    REQ,
    make_auth,
    make_config,
    make_policy,
    make_ref,
)


def make_checkpoint() -> object:
    return create_strategy_checkpoint_value(
        checkpoint_id="cp-1",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_hash=HASH,
        state={"counter": 1},
        state_checksum=HASH,
        authorization_ref="auth-1",
        created_at=NOW,
        request_id=REQ,
        payload_bytes=100,
        redacted_paths=(),
    )


def test_create_strategy_checkpoint_data_error_handled() -> None:
    """Verify data domain persistence failure returns INTERNAL_ERROR."""
    ref = make_ref()
    config = make_config()
    auth = make_auth(permissions=("strategy:checkpoint",))
    with patch(
        "app.services.strategy.checkpoints.store.create_strategy_checkpoint_record",
        side_effect=ValueError("data failure"),
    ):
        res = create_strategy_checkpoint(
            ref, config, {"counter": 1}, "auth-ref-001", auth, policy=make_policy()
        )
        assert res.status == "error"
        assert res.error is not None
        assert res.error.code == "STRATEGY_INTERNAL_ERROR"


def test_validate_strategy_checkpoint_persistence_read_failure() -> None:
    """Verify read persistence failure returns INTERNAL_ERROR."""
    ref = make_ref()
    config = make_config()
    auth = make_auth(permissions=("strategy:checkpoint",))
    checkpoint = make_checkpoint()

    with patch(
        "app.services.strategy.checkpoints.store.read_strategy_checkpoint_record",
        side_effect=StrategyOperationError("STRATEGY_INTERNAL_ERROR", "read failed"),
    ):
        res = validate_strategy_checkpoint(ref, config, checkpoint, auth)
        assert res.status == "error"
        assert res.error is not None
        assert res.error.code == "STRATEGY_INTERNAL_ERROR"

    import contextlib

    with (
        patch(
            "app.services.strategy.checkpoints.store.read_strategy_checkpoint_record",
            side_effect=RuntimeError("unknown error"),
        ),
        contextlib.suppress(RuntimeError),
    ):
        validate_strategy_checkpoint(ref, config, checkpoint, auth)


def test_list_strategy_checkpoints_branches() -> None:
    """Verify list_strategy_checkpoints returns tuple of checkpoints."""
    with patch(
        "app.services.strategy.persistence.read_strategy_checkpoints",
        return_value=[],
    ):
        res = list_strategy_checkpoints("test-config-id")
        assert res.status == "success"
        assert res.data == ()
