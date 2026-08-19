"""Contract and migration-structure tests for the Simulation Workbench."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.api.workstation.simulation_workbench import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_VIEWPORT_BEFORE,
    MAX_BATCH_CONCURRENCY,
    MAX_BATCH_ITEMS,
    MAX_PAGE_SIZE,
    MAX_SEEK_TICKS,
    MAX_STEP_TICKS,
    MAX_TAG_LENGTH,
    MAX_TAGS,
    MAX_TRADE_PAGE_SIZE,
    MAX_VIEWPORT_BEFORE,
    VIEWPORT_AFTER,
    RunCatalogueEntry,
    get_simulation_workbench_migration_steps,
)
from app.services.api.workstation.simulation_workbench.schemas import (
    BatchCreateRequest,
    BatchRunSpec,
    LiveSessionBranchRequest,
    LiveSessionCommandRequest,
    RunAnnotationRequest,
    SeekRequest,
    StepRequest,
    ViewportQuery,
)
from pydantic import ValidationError

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _entry(**overrides: object) -> RunCatalogueEntry:
    """Build one valid catalogue entry."""
    values: dict[str, object] = {
        "run_id": "run-1",
        "principal_id": "principal-1",
        "origin_kind": "canonical_job",
        "status": "queued",
        "evidence_class": "canonical",
        "created_at": _NOW,
    }
    values.update(overrides)
    return RunCatalogueEntry(**values)  # type: ignore[arg-type]


def test_catalogue_entry_is_frozen_and_extra_forbidden() -> None:
    """Unknown fields are refused and rows are immutable."""
    entry = _entry()
    with pytest.raises(ValidationError):
        RunCatalogueEntry(
            **{
                **_entry().model_dump(),
                "invented": "field",
            }
        )
    with pytest.raises(ValidationError):
        entry.run_id = "changed"


def test_catalogue_entry_rejects_untrimmed_identity_and_bad_tags() -> None:
    """Identity must be trimmed and tags bounded, unique, and trimmed."""
    with pytest.raises(ValidationError):
        _entry(run_id=" run-1")
    with pytest.raises(ValidationError):
        _entry(tags=("ok", "ok"))
    with pytest.raises(ValidationError):
        _entry(tags=("x" * (MAX_TAG_LENGTH + 1),))
    with pytest.raises(ValidationError):
        _entry(tags=tuple(f"tag-{index}" for index in range(MAX_TAGS + 1)))
    assert _entry(tags=("ok",)).tags == ("ok",)


def test_catalogue_entry_rejects_out_of_catalogue_enums() -> None:
    """Origin, status, evidence, and archive values are closed sets."""
    for field, value in (
        ("origin_kind", "mystery"),
        ("status", "paused"),
        ("evidence_class", "secret"),
        ("archive_state", "deleted"),
    ):
        with pytest.raises(ValidationError):
            _entry(**{field: value})


def test_viewport_never_requests_future_rows() -> None:
    """``after`` is contractually zero and ``before`` is bounded."""
    query = ViewportQuery()
    assert query.after == VIEWPORT_AFTER == 0
    assert query.before == DEFAULT_VIEWPORT_BEFORE
    with pytest.raises(ValidationError):
        ViewportQuery(before=MAX_VIEWPORT_BEFORE + 1)
    with pytest.raises(ValidationError):
        ViewportQuery(after=1)


def test_step_and_seek_bounds() -> None:
    """Tick advancement and seeking are bounded by contract."""
    assert StepRequest(ticks=MAX_STEP_TICKS).ticks == MAX_STEP_TICKS
    with pytest.raises(ValidationError):
        StepRequest(ticks=MAX_STEP_TICKS + 1)
    assert SeekRequest(target_cursor=MAX_SEEK_TICKS).target_cursor == MAX_SEEK_TICKS
    with pytest.raises(ValidationError):
        SeekRequest(target_cursor=-1)


def test_command_discriminators_are_the_exact_six() -> None:
    """Only the six frozen command discriminators are accepted."""
    from typing import get_args

    from app.services.api.workstation.simulation_workbench.schemas import (
        CommandType,
    )

    assert set(get_args(CommandType)) == {
        "submit_order",
        "modify_pending_order",
        "cancel_pending_order",
        "close_position",
        "reduce_position",
        "close_all_practice_exposure",
    }
    assert LiveSessionCommandRequest(command="close_position").command == (
        "close_position"
    )
    with pytest.raises(ValidationError):
        LiveSessionCommandRequest(command="invent_fill")


def _batch_item() -> BatchRunSpec:
    """Build one bounded batch item carrying its measurement window.

    Returns:
        Validated batch run specification.
    """
    return BatchRunSpec(
        symbol="EURUSD",
        timeframe="H1",
        strategy_id="s",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 2, 1, tzinfo=UTC),
    )


def test_batch_request_bounds() -> None:
    """Batch items and concurrency are bounded."""
    assert MAX_BATCH_ITEMS == 100
    assert MAX_BATCH_CONCURRENCY == 8
    item = _batch_item()
    request = BatchCreateRequest(items=(item,), concurrency=4)
    assert request.concurrency == 4
    with pytest.raises(ValidationError):
        BatchCreateRequest(
            items=tuple(_batch_item() for _ in range(MAX_BATCH_ITEMS + 1))
        )
    with pytest.raises(ValidationError):
        BatchCreateRequest(items=(item,), concurrency=MAX_BATCH_CONCURRENCY + 1)
    with pytest.raises(ValidationError):
        BatchCreateRequest(items=())


def test_branch_overrides_and_annotations_are_bounded() -> None:
    """Override and annotation collections are bounded and trimmed."""
    with pytest.raises(ValidationError):
        LiveSessionBranchRequest(overrides={"a": "  "})
    with pytest.raises(ValidationError):
        RunAnnotationRequest(tags=("dup", "dup"))
    assert RunAnnotationRequest().tags == ()


def test_pagination_constants_match_the_frozen_contract() -> None:
    """Pagination constants equal the shared contract values."""
    assert DEFAULT_PAGE_SIZE == 50
    assert MAX_PAGE_SIZE == 200
    assert MAX_TRADE_PAGE_SIZE == 500


def test_migration_steps_are_additive_with_identity_bound_checksums() -> None:
    """Migration ids are immutable and checksums bind their statements."""
    steps = get_simulation_workbench_migration_steps()
    assert len(steps) == 1
    step = steps[0]
    assert step.migration_id == "api-0011"
    assert step.domain == "api"
    statements = "\n".join(step.statements)
    for table in (
        "api_simulation_results",
        "api_simulation_sessions",
        "api_simulation_batches",
        "api_simulation_batch_items",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in statements
    assert "DROP TABLE" not in statements.upper()
    assert "ALTER TABLE" not in statements.upper()
    assert len(step.checksum) == 64
