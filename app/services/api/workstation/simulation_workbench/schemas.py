"""Simulation Workbench frozen request and catalogue contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from app.services.api.contracts.models import _BaseApiContract, _validate_non_empty

#: Catalogue pagination defaults and bounds.
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MAX_TRADE_PAGE_SIZE = 500

#: Batch resource bounds.
MAX_BATCH_ITEMS = 100
MAX_BATCH_CONCURRENCY = 8

#: Annotation tag bounds.
MAX_TAGS = 16
MAX_TAG_LENGTH = 64

#: Live-session viewport bounds. The viewport never exposes rows after the
#: server cursor, so ``after`` is fixed at zero by contract.
DEFAULT_VIEWPORT_BEFORE = 300
MAX_VIEWPORT_BEFORE = 5_000
VIEWPORT_AFTER: Literal[0] = 0

#: Live-session advancement bounds.
MAX_STEP_TICKS = 10_000
MAX_SEEK_TICKS = 100_000

OriginKind = Literal["canonical_job", "batch", "practice", "reproduction", "portfolio"]
CatalogueStatus = Literal["queued", "running", "completed", "failed", "cancelled"]
EvidenceClass = Literal[
    "canonical", "practice", "advisory", "playback", "fast_research"
]
ArchiveState = Literal["active", "archived"]

CommandType = Literal[
    "submit_order",
    "modify_pending_order",
    "cancel_pending_order",
    "close_position",
    "reduce_position",
    "close_all_practice_exposure",
]

_MAX_IDENTIFIER = 128
_MAX_TEXT = 2_000
_MAX_OVERRIDES = 32


class RunCatalogueEntry(_BaseApiContract):
    """Principal-scoped durable catalogue row for one Simulation run.

    The row stores only identity, ownership, immutable owner references,
    and mutable annotations. No calculated metric, trade ledger, full
    report, or full Simulation result is ever stored.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.run_catalogue_entry.v1"] = "api.run_catalogue_entry.v1"
    run_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER)
    principal_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER)
    origin_kind: OriginKind
    origin_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    job_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    batch_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    session_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    strategy_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    strategy_version: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    strategy_label: str | None = Field(default=None, max_length=_MAX_TEXT)
    symbols: tuple[str, ...] = Field(default=(), max_length=16)
    timeframe: str | None = Field(default=None, max_length=8)
    measurement_start: datetime | None = None
    measurement_end: datetime | None = None
    status: CatalogueStatus
    result_ref: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    report_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    report_ref: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    artifact_manifest_ref: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    quality_status: str | None = Field(default=None, max_length=64)
    evidence_class: EvidenceClass
    created_at: datetime
    completed_at: datetime | None = None
    name: str | None = Field(default=None, max_length=_MAX_TEXT)
    alias: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    description: str | None = Field(default=None, max_length=_MAX_TEXT)
    tags: tuple[str, ...] = Field(default=(), max_length=MAX_TAGS)
    run_reason: str | None = Field(default=None, max_length=_MAX_TEXT)
    archive_state: ArchiveState = "active"

    @field_validator("run_id", "principal_id")
    @classmethod
    def _validate_identifier(cls, value: str) -> str:
        """Validate one trimmed non-empty identifier.

        Returns:
            Validated identifier.
        """
        return _validate_non_empty(value, "identifier")

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate bounded, unique, trimmed tags.

        Returns:
            Validated tags.

        Raises:
            ValueError: If a tag is empty, untrimmed, or too long.
        """
        for tag in value:
            if not tag or tag != tag.strip():
                msg = "tags must be non-empty and trimmed"
                raise ValueError(msg)
            if len(tag) > MAX_TAG_LENGTH:
                msg = f"tags must be at most {MAX_TAG_LENGTH} characters"
                raise ValueError(msg)
        if len(set(value)) != len(value):
            msg = "tags must be unique"
            raise ValueError(msg)
        return value


class LiveSessionCreateRequest(_BaseApiContract):
    """Request to open one typed live session over a completed run."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.live_session_create_request.v1"] = (
        "api.live_session_create_request.v1"
    )
    run_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER)
    mode: Literal["practice"] = "practice"
    durable: bool = False

    @field_validator("run_id")
    @classmethod
    def _validate_run(cls, value: str) -> str:
        """Validate one trimmed run identifier.

        Returns:
            Validated identifier.
        """
        return _validate_non_empty(value, "run_id")


class ViewportQuery(_BaseApiContract):
    """Bounded backwards-looking market viewport query.

    ``after`` is frozen at zero: the viewport never exposes rows beyond
    the server cursor, so no future row can ever be requested.
    """

    before: int = Field(default=DEFAULT_VIEWPORT_BEFORE, ge=1, le=MAX_VIEWPORT_BEFORE)
    after: Literal[0] = VIEWPORT_AFTER


class StepRequest(_BaseApiContract):
    """Request to advance one live session by a bounded tick count."""

    ticks: int = Field(ge=1, le=MAX_STEP_TICKS)


class SeekRequest(_BaseApiContract):
    """Request to move one live session forward to an absolute cursor."""

    target_cursor: int = Field(ge=0)


class LiveSessionCommandRequest(_BaseApiContract):
    """One manual command against a live practice session.

    Every response is authoritative: the gateway returns the owner
    receipt and refreshed session state and never invents a fill.
    """

    command: CommandType
    symbol: str | None = Field(default=None, max_length=32)
    side: Literal["buy", "sell"] | None = None
    volume: str | None = Field(default=None, max_length=32)
    price: str | None = Field(default=None, max_length=32)
    stop_loss: str | None = Field(default=None, max_length=32)
    take_profit: str | None = Field(default=None, max_length=32)
    order_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    position_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    reason: str | None = Field(default=None, max_length=_MAX_TEXT)


class LiveSessionBranchRequest(_BaseApiContract):
    """Request to fork one live session into an advisory branch."""

    overrides: Mapping[str, str] = Field(default_factory=dict)

    @field_validator("overrides")
    @classmethod
    def _validate_overrides(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate a bounded, trimmed override mapping.

        Returns:
            Validated overrides.

        Raises:
            ValueError: If too many entries or an untrimmed key/value exists.
        """
        if len(value) > _MAX_OVERRIDES:
            msg = f"overrides must contain at most {_MAX_OVERRIDES} entries"
            raise ValueError(msg)
        for key, item in value.items():
            if not key or key != key.strip() or not item or item != item.strip():
                msg = "override keys and values must be non-empty and trimmed"
                raise ValueError(msg)
        return value


class BatchRunSpec(_BaseApiContract):
    """One run specification inside a batch request."""

    symbol: str = Field(min_length=1, max_length=32)
    timeframe: str = Field(min_length=1, max_length=8)
    strategy_id: str = Field(min_length=1, max_length=100)
    parameters: Mapping[str, str] = Field(default_factory=dict)


class BatchCreateRequest(_BaseApiContract):
    """Request to execute a bounded batch of canonical runs."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.simulation_batch_create_request.v1"] = (
        "api.simulation_batch_create_request.v1"
    )
    items: tuple[BatchRunSpec, ...] = Field(min_length=1, max_length=MAX_BATCH_ITEMS)
    concurrency: int = Field(default=1, ge=1, le=MAX_BATCH_CONCURRENCY)
    name: str | None = Field(default=None, max_length=_MAX_TEXT)


class RunAnnotationRequest(_BaseApiContract):
    """Mutable principal-owned annotation for one catalogue run."""

    name: str | None = Field(default=None, max_length=_MAX_TEXT)
    alias: str | None = Field(default=None, max_length=_MAX_IDENTIFIER)
    description: str | None = Field(default=None, max_length=_MAX_TEXT)
    tags: tuple[str, ...] = Field(default=(), max_length=MAX_TAGS)
    run_reason: str | None = Field(default=None, max_length=_MAX_TEXT)

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate bounded, unique, trimmed tags.

        Returns:
            Validated tags.

        Raises:
            ValueError: If a tag is empty, untrimmed, or too long.
        """
        for tag in value:
            if not tag or tag != tag.strip() or len(tag) > MAX_TAG_LENGTH:
                msg = "tags must be non-empty, trimmed, and bounded"
                raise ValueError(msg)
        if len(set(value)) != len(value):
            msg = "tags must be unique"
            raise ValueError(msg)
        return value


class RunArchiveRequest(_BaseApiContract):
    """Request to change one run's archive state.

    Archiving affects catalogue metadata only; immutable run artifacts
    are never deleted.
    """

    archive_state: ArchiveState


__all__ = (
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_VIEWPORT_BEFORE",
    "MAX_BATCH_CONCURRENCY",
    "MAX_BATCH_ITEMS",
    "MAX_PAGE_SIZE",
    "MAX_SEEK_TICKS",
    "MAX_STEP_TICKS",
    "MAX_TAGS",
    "MAX_TAG_LENGTH",
    "MAX_TRADE_PAGE_SIZE",
    "MAX_VIEWPORT_BEFORE",
    "VIEWPORT_AFTER",
    "ArchiveState",
    "BatchCreateRequest",
    "BatchRunSpec",
    "CatalogueStatus",
    "CommandType",
    "EvidenceClass",
    "LiveSessionBranchRequest",
    "LiveSessionCommandRequest",
    "LiveSessionCreateRequest",
    "OriginKind",
    "RunAnnotationRequest",
    "RunArchiveRequest",
    "RunCatalogueEntry",
    "SeekRequest",
    "StepRequest",
    "ViewportQuery",
)
