"""WF-STR-008 mutation-result publication integration."""

# ruff: noqa: PT018

from pathlib import Path

from app.services.strategy import StrategyLifecycleStatus, register_strategy_version
from app.utils import logger

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import make_auth, make_policy

_SHA256_LENGTH = 64


def test_registration_workflow(tmp_path: Path) -> None:
    """Commit registry and direct mutation truth in one workflow."""
    logger.debug("Testing WF-STR-008 registration workflow output boundary")
    with storage_context(tmp_path):
        outcome = register_strategy_version(
            make_registration(), make_auth(), make_policy()
        )
    assert outcome.status == "success"
    mutation = outcome.data
    assert mutation is not None
    assert mutation.contract_version == "v1"
    assert mutation.schema_id == "strategy.mutation_result.v1"
    assert mutation.mutation_type == "REGISTER_VERSION"
    assert mutation.status == "ACCEPTED"
    assert mutation.validated_ref is not None
    assert mutation.validated_config is None
    assert len(mutation.record_hash or "") == _SHA256_LENGTH
    assert mutation.record_ref == "mean-reversion@1.0.0"
    assert mutation.completed_at.tzinfo is not None


def test_registration_workflow_retry_is_idempotent(tmp_path: Path) -> None:
    """Verify a repeated command id completes without duplicating the mutation."""
    logger.debug("Testing WF-STR-008 idempotent retry")
    with storage_context(tmp_path):
        first = register_strategy_version(
            make_registration(), make_auth(), make_policy()
        )
        retry = register_strategy_version(
            make_registration(), make_auth(), make_policy()
        )
    assert first.data is not None and first.data.status == "ACCEPTED"
    assert retry.data is not None and retry.data.status == "IDEMPOTENT"
    assert retry.data.mutation_id == first.data.mutation_id


def test_registration_workflow_rejects_unapproved_lifecycle(tmp_path: Path) -> None:
    """Verify an unapproved lifecycle fails closed with no validated payload."""
    logger.debug("Testing WF-STR-008 fail-closed lifecycle rejection")
    request = make_registration().model_copy(
        update={"lifecycle_status": StrategyLifecycleStatus.DRAFT}
    )
    with storage_context(tmp_path):
        outcome = register_strategy_version(request, make_auth(), make_policy())
    assert outcome.status == "success"
    mutation = outcome.data
    assert mutation is not None
    assert mutation.status == "REJECTED"
    assert mutation.reason_codes == ("LIFECYCLE_NOT_APPROVED",)
    assert mutation.validated_ref is None
    assert mutation.validated_config is None
    assert mutation.record_hash is None


def test_registration_workflow_emits_no_storage_object(tmp_path: Path) -> None:
    """Verify persistence objects never cross the mutation-result boundary."""
    logger.debug("Testing WF-STR-008 storage-object boundary")
    with storage_context(tmp_path):
        outcome = register_strategy_version(
            make_registration(), make_auth(), make_policy()
        )
    assert outcome.data is not None
    payload = outcome.data.model_dump(mode="json")
    forbidden = {"connection", "cursor", "session", "engine", "rows", "statements"}
    assert not forbidden & set(payload)
