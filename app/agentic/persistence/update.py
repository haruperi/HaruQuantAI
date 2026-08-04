"""Update operations for Agentic-owned relational records."""

from __future__ import annotations

from app.agentic.persistence.create import _execute, _field, _model_value
from app.utils import get_logger

logger = get_logger(__name__)


def update_workflow_run_record(
    store: object,
    *,
    key: str,
    value: object,
    expected_revision: int,
) -> None:
    """Compare-and-swap one Agentic workflow run.

    Args:
        store: Opaque Agentic relational persistence handle.
        key: Immutable workflow-run identifier.
        value: Replacement workflow-run state.
        expected_revision: Caller-observed owner revision.

    Raises:
        ValueError: If identity, target revision, or stored revision conflicts.
    """
    logger.debug("Updating Agentic workflow run persistence record")
    run = _model_value(store, "workflow-run", value)
    if _field(run, "run_id") != key:
        raise ValueError("Agentic workflow run identity is inconsistent")
    if _field(run, "revision") != expected_revision + 1:
        raise ValueError("Agentic workflow target revision is inconsistent")
    result = _execute(
        (
            "UPDATE agentic_workflow_runs SET state=?, current_node=?, sequence=?, "
            "revision=?, attempts=?, updated_at=?, deadline_at=?, terminal_reason=? "
            "WHERE run_id=? AND revision=?",
        ),
        (
            (
                _field(run, "state"),
                _field(run, "current_node"),
                _field(run, "sequence"),
                _field(run, "revision"),
                _field(run, "attempts"),
                _field(run, "updated_at"),
                _field(run, "deadline_at"),
                run.get("terminal_reason"),
                key,
                expected_revision,
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("Agentic workflow revision conflict")


__all__ = ["update_workflow_run_record"]
