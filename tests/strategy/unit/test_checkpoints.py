"""Persisted Strategy checkpoint tests."""

# ruff: noqa: PT018
from unittest.mock import patch

from app.composition.logging import get_logger
from app.services.strategy import (
    create_strategy_checkpoint,
    validate_strategy_checkpoint,
)

from tests.strategy.unit.test_models import make_auth, make_config, make_ref

logger = get_logger(__name__)


def test_checkpoint_is_bounded_redacted_and_persisted() -> None:
    """Verify checkpoint creation redacts secrets and validates state."""
    logger.debug("Testing Strategy checkpoint creation and validation")
    auth = make_auth(checkpoint=True)
    saved_records: list[object] = []

    def mock_create(checkpoint: object) -> None:
        """Collect created checkpoint objects.

        Args:
            checkpoint: Persisted checkpoint object.

        Returns:
            None.
        """
        saved_records.append(checkpoint)

    def mock_read(checkpoint_id: str, request_id: str) -> tuple[dict[str, str], ...]:
        """Return serialized checkpoint state for testing.

        Args:
            checkpoint_id: Unique checkpoint record identifier.
            request_id: Tracing request identifier.

        Returns:
            Single-row tuple containing checkpoint_json string.
        """
        return ({"checkpoint_json": saved_records[0].model_dump_json()},)

    with (
        patch("app.services.strategy.checkpoints.store._ensure_strategy_storage"),
        patch(
            "app.services.strategy.checkpoints.store.create_strategy_checkpoint_record",
            side_effect=mock_create,
        ),
        patch(
            "app.services.strategy.checkpoints.store.read_strategy_checkpoint_record",
            side_effect=mock_read,
        ),
    ):
        created = create_strategy_checkpoint(
            make_ref(),
            make_config(),
            {"counter": 1, "token": "secret"},
            "checkpoint-auth",
            auth,
        )
        assert created.data is not None
        restored = validate_strategy_checkpoint(
            created.data, make_ref(), make_config(), auth
        )

    assert restored.status == "success"
    assert created.data is not None and created.data.redacted_paths == ("token",)


def test_checkpoint_hash_mismatch_fails_before_restore() -> None:
    """Verify a modified caller checkpoint cannot restore stored state."""
    logger.debug("Testing Strategy checkpoint checksum mismatch")
    auth = make_auth(checkpoint=True)
    saved_records: list[object] = []

    def mock_create(checkpoint: object) -> None:
        """Collect created checkpoint objects.

        Args:
            checkpoint: Persisted checkpoint object.

        Returns:
            None.
        """
        saved_records.append(checkpoint)

    def mock_read(checkpoint_id: str, request_id: str) -> tuple[dict[str, str], ...]:
        """Return serialized checkpoint state for testing.

        Args:
            checkpoint_id: Unique checkpoint record identifier.
            request_id: Tracing request identifier.

        Returns:
            Single-row tuple containing checkpoint_json string.
        """
        return ({"checkpoint_json": saved_records[0].model_dump_json()},)

    with (
        patch("app.services.strategy.checkpoints.store._ensure_strategy_storage"),
        patch(
            "app.services.strategy.checkpoints.store.create_strategy_checkpoint_record",
            side_effect=mock_create,
        ),
        patch(
            "app.services.strategy.checkpoints.store.read_strategy_checkpoint_record",
            side_effect=mock_read,
        ),
    ):
        created = create_strategy_checkpoint(
            make_ref(), make_config(), {"counter": 1}, "checkpoint-auth", auth
        )
        assert created.data is not None
        tampered = created.data.model_copy(update={"state_checksum": "b" * 64})
        restored = validate_strategy_checkpoint(
            tampered, make_ref(), make_config(), auth
        )

    assert restored.status == "error"
