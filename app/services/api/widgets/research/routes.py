"""Authenticated Research workbench HTTP boundaries.

A complete Research pass exceeds the endpoint deadline, so the run surface is a
job: submission returns an identity immediately and progress is observed by
polling or by consuming the ordered event stream. Every read is an API-owned
projection of the registered Research report — the gateway performs no Research
calculation, and no browser request carries an artifact path or resource limit.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable, Mapping
from typing import TYPE_CHECKING, Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from app.services.api import build_stream_event
from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    require_permission,
    run_idempotent_write,
    run_idempotent_write_async,
)
from app.services.api.widgets.research import presets, views
from app.services.api.widgets.research.orchestration import capture_artifact_auth
from app.services.api.widgets.research.projections import (
    STAGE_VIEWS,
    project_report,
)
from app.services.api.widgets.research.schemas import (
    ResearchAutomationRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    ResearchComparisonRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    ResearchExpectancyCreateRequest,  # noqa: TC001 - FastAPI runtime annotation.
    ResearchExpectancyTransitionRequest,  # noqa: TC001 - FastAPI runtime annotation.
    ResearchExperimentCreateRequest,  # noqa: TC001 - FastAPI runtime annotation.
    ResearchRunCreateRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    ResearchRunRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    ResearchStressScenarioCreateRequest,  # noqa: TC001 - FastAPI runtime annotation.
)
from app.services.research import get_stress_scenario_catalog, run_edge_lab_profile
from app.utils import generate_id, get_logger

if TYPE_CHECKING:
    from app.services.api.widgets.research.registry import (
        ResearchRun,
        ResearchWorkbenchRegistry,
    )

type AuthContext = Any
type StandardResponse[T] = Any
type _ResearchSource = Callable[..., object]

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["research"])
_STREAM_ROUTE = "/api/v1/research/runs/{run_id}/events"
_CREATE_RUN_ROUTE = "/api/v1/research/experiments/{experiment_id}/runs"
_CREATE_AUTOMATION_ROUTE = "/api/v1/research/automation"
_CREATE_EXPECTANCY_ROUTE = "/api/v1/research/expectancy"
_CREATE_STRESS_ROUTE = "/api/v1/research/stress-scenarios"
_EXPECTANCY_TRANSITION_ROUTE = "/api/v1/research/expectancy/{profile_id}/transition"


def _require_idempotency(value: str | None) -> str:
    """Return one non-empty idempotency key or reject the governed write.

    Args:
        value: Caller-supplied header value.

    Returns:
        Normalized non-empty key.

    Raises:
        HTTPException: If the required key is absent or blank.
    """
    if value is None or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    return value.strip()


def _research_source() -> _ResearchSource:
    """Fail closed until canonical composition injects the workbench registry.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="RESEARCH_RUNTIME_UNAVAILABLE",
    )


def _registry(source: _ResearchSource) -> ResearchWorkbenchRegistry:
    """Return the composed workbench registry or fail closed.

    Args:
        source: Injected Research workbench dispatcher.

    Returns:
        Composed workbench registry.

    Raises:
        HTTPException: If the registry is not composed.
    """
    try:
        return cast("ResearchWorkbenchRegistry", source("registry"))
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RESEARCH_RUNTIME_UNAVAILABLE",
        ) from error


def _require_run(
    source: _ResearchSource, run_id: str, auth: AuthContext
) -> ResearchRun:
    """Return one owned run or fail closed.

    Args:
        source: Injected Research workbench dispatcher.
        run_id: Run identity.
        auth: Authenticated principal.

    Returns:
        Owned run record.

    Raises:
        HTTPException: If the run is unknown or owned by another principal.
    """
    run = _registry(source).get_run(run_id, principal_id=auth.principal_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESEARCH_RUN_NOT_FOUND",
        )
    return run


def _require_experiment(
    source: _ResearchSource, experiment_id: str, auth: AuthContext
) -> object:
    """Return one owned experiment or fail closed.

    Args:
        source: Injected Research workbench dispatcher.
        experiment_id: Experiment identity.
        auth: Authenticated principal.

    Returns:
        Owned experiment record.

    Raises:
        HTTPException: If the experiment is unknown or owned by another
            principal.
    """
    experiment = _registry(source).get_experiment(
        experiment_id, principal_id=auth.principal_id
    )
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESEARCH_EXPERIMENT_NOT_FOUND",
        )
    return experiment


def _queue_run(
    *,
    registry: ResearchWorkbenchRegistry,
    auth: AuthContext,
    experiment: object,
    request: ResearchRunCreateRequest,
    symbol: str,
    batch_id: str | None = None,
) -> ResearchRun:
    """Resolve the effective stage selection and queue one background run.

    Args:
        registry: Composed workbench registry.
        auth: Authenticated principal.
        experiment: Owning experiment record.
        request: Validated safe run-create request.
        symbol: Instrument the run analyzes.
        batch_id: Owning automation batch, when the run came from one.

    Returns:
        Queued run record.

    Raises:
        HTTPException: If the preset, stage selection, or an approved override
            is rejected.
    """
    try:
        selected = presets.resolve_selected_stages(
            request.preset, request.selected_stages
        )
        # Resolving the configuration here surfaces a bad override as a 422 at
        # submission rather than as a background failure minutes later.
        presets.build_preset_config(request, symbol=symbol, selected_stages=selected)
    except presets.PresetError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    selection = request.dataset.model_copy(update={"symbol": symbol})
    return registry.submit_run(
        principal_id=auth.principal_id,
        experiment_id=str(cast("Any", experiment).experiment_id),
        hypothesis=request.hypothesis or str(cast("Any", experiment).hypothesis),
        symbol=symbol,
        timeframe=request.dataset.timeframe,
        preset=request.preset,
        selected_stages=selected,
        reason=request.reason,
        force_rerun=request.force_rerun,
        batch_id=batch_id,
        request_material={
            "request": request.model_copy(update={"dataset": selection}),
            "dataset": {
                "source_id": selection.source_id,
                "start": selection.start,
                "end": selection.end,
                "bar_limit": selection.bar_limit,
                "asset_class": selection.asset_class,
            },
            "auth": capture_artifact_auth(auth),
            "save_artifacts": request.save_artifacts,
        },
    )


@router.post("/run", response_model=None)
def _run_research(
    request: ResearchRunRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> StandardResponse[object]:
    """Delegate one authenticated bounded run to Research.

    Args:
        request: Validated API-owned Research request.
        auth: Authenticated human principal.

    Returns:
        Standard response containing the registered advisory Research report.
    """
    logger.info("Delegating authenticated Research run")
    require_human_permission(auth, "research:run")
    return run_edge_lab_profile(
        request.dataset,
        hypothesis=request.hypothesis,
        config=request.config,
    )


@router.get("/presets", response_model=None)
def _list_presets(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return every server-owned Research preset.

    Args:
        auth: Authenticated principal.

    Returns:
        Preset catalogue including approved override keys and stage vocabulary.
    """
    require_permission(auth, "research:read")
    return {
        "presets": list(presets.list_research_presets()),
        "stages": list(presets.get_stage_vocabulary()),
        "stage_views": list(STAGE_VIEWS),
        "stress_scenarios": list(get_stress_scenario_catalog()),
    }


@router.get("/dashboard", response_model=None)
def _dashboard(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Return the research ledger for the workbench entry page.

    Args:
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Experiments, recent runs, readiness distribution, and study counts.
    """
    require_permission(auth, "research:read")
    return views.dashboard_view(_registry(source), principal_id=auth.principal_id)


@router.post("/experiments", response_model=None, status_code=status.HTTP_201_CREATED)
def _create_experiment(
    request: ResearchExperimentCreateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Create one experiment ledger entry.

    Args:
        request: Validated experiment creation request.
        auth: Authenticated human principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Created experiment detail.
    """
    require_human_permission(auth, "research:run")
    experiment = _registry(source).create_experiment(
        principal_id=auth.principal_id,
        name=request.name,
        hypothesis=request.hypothesis,
        notes=request.notes,
        tags=request.tags,
    )
    return views.experiment_detail(experiment, ())


@router.get("/experiments", response_model=None)
def _list_experiments(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Return every experiment owned by the caller.

    Args:
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Owned experiment summaries, newest first.
    """
    require_permission(auth, "research:read")
    registry = _registry(source)
    experiments = registry.list_experiments(principal_id=auth.principal_id)
    return {
        "experiments": [
            dict(
                experiment.summary(
                    run_count=len(
                        registry.list_runs(
                            principal_id=auth.principal_id,
                            experiment_id=experiment.experiment_id,
                        )
                    ),
                    latest=(
                        dict(
                            views.run_summary(
                                registry.list_runs(
                                    principal_id=auth.principal_id,
                                    experiment_id=experiment.experiment_id,
                                )[0]
                            )
                        )
                        if registry.list_runs(
                            principal_id=auth.principal_id,
                            experiment_id=experiment.experiment_id,
                        )
                        else None
                    ),
                )
            )
            for experiment in experiments
        ]
    }


@router.get("/experiments/{experiment_id}", response_model=None)
def _get_experiment(
    experiment_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Return one owned experiment with its run ledger.

    Args:
        experiment_id: Experiment identity.
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Experiment detail including every retained run.
    """
    require_permission(auth, "research:read")
    experiment = _require_experiment(source, experiment_id, auth)
    runs = _registry(source).list_runs(
        principal_id=auth.principal_id, experiment_id=experiment_id
    )
    return views.experiment_detail(cast("Any", experiment), runs)


@router.post(
    "/experiments/{experiment_id}/runs",
    response_model=None,
    status_code=status.HTTP_202_ACCEPTED,
)
async def _create_run(
    experiment_id: str,
    request: ResearchRunCreateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Queue one background Research run for an owned experiment.

    Args:
        experiment_id: Owning experiment identity.
        request: Validated safe run-create request.
        auth: Authenticated human principal.
        source: Injected Research workbench dispatcher.
        idempotency_key: Required durable replay key.

    Returns:
        Accepted run detail carrying its identity and queued status.
    """
    require_human_permission(auth, "research:run")
    key = _require_idempotency(idempotency_key)
    experiment = _require_experiment(source, experiment_id, auth)
    request_material = {
        "experiment_id": experiment_id,
        "request": request.model_dump(mode="json"),
    }

    def submit() -> object:
        """Queue the owner run exactly once after reservation.

        Returns:
            Accepted run detail.
        """
        run = _queue_run(
            registry=_registry(source),
            auth=auth,
            experiment=experiment,
            request=request,
            symbol=request.dataset.symbol,
        )
        return views.run_detail(run)

    return await run_idempotent_write_async(
        principal_id=str(auth.principal_id),
        method="POST",
        route=_CREATE_RUN_ROUTE,
        key=key,
        request_material=request_material,
        request_id=generate_id("req"),
        operation=lambda: asyncio.to_thread(submit),
    )


@router.get("/runs", response_model=None)
def _list_runs(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    experiment_id: str | None = None,
    batch_id: str | None = None,
) -> object:
    """Return the caller's retained runs, newest first.

    Failed, cancelled, and inconclusive runs are included deliberately.

    Args:
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.
        experiment_id: Optional experiment filter.
        batch_id: Optional automation batch filter.

    Returns:
        Owned run summaries.
    """
    require_permission(auth, "research:read")
    runs = _registry(source).list_runs(
        principal_id=auth.principal_id,
        experiment_id=experiment_id,
        batch_id=batch_id,
    )
    return {"runs": [dict(views.run_summary(run)) for run in runs]}


@router.post("/runs/compare", response_model=None)
def _compare_runs(
    request: ResearchComparisonRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Compare two or more owned runs.

    Args:
        request: Validated comparison request.
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Server-derived comparison across readiness, metrics, studies, stages,
        warnings, and provenance.
    """
    require_permission(auth, "research:read")
    runs = [_require_run(source, run_id, auth) for run_id in request.run_ids]
    return views.comparison_view(runs)


@router.get("/runs/{run_id}", response_model=None)
def _get_run(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Return one owned run with its header, stage status, and provenance.

    Args:
        run_id: Run identity.
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Run detail.
    """
    require_permission(auth, "research:read")
    return views.run_detail(_require_run(source, run_id, auth))


@router.get("/runs/{run_id}/report", response_model=None)
def _get_run_report(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Return the registered report for the secondary diagnostic viewer.

    Args:
        run_id: Run identity.
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Registered report, or an explicit unavailable state.
    """
    require_permission(auth, "research:read")
    run = _require_run(source, run_id, auth)
    if run.report is None:
        return {
            "available": False,
            "reason": "NO_REPORT_PRODUCED",
            "status": run.status,
            "report": None,
        }
    return {
        "available": True,
        "reason": None,
        "status": run.status,
        "report": dict(project_report(run.report)),
    }


@router.get("/runs/{run_id}/stages/{stage}", response_model=None)
def _get_run_stage(
    run_id: str,
    stage: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    scenario_id: str | None = None,
    profile_id: str | None = None,
) -> object:
    """Return one navigable stage view for an owned run.

    Args:
        run_id: Run identity.
        stage: Navigable stage view name.
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.
        scenario_id: Optional stress scenario identity for the stress stage.
        profile_id: Optional expectancy profile identity for the stress stage.

    Returns:
        Stage view carrying explicit state, evidence, and warnings.

    Raises:
        HTTPException: If the stage view is not registered.
    """
    require_permission(auth, "research:read")
    run = _require_run(source, run_id, auth)
    if stage not in STAGE_VIEWS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESEARCH_STAGE_UNKNOWN",
        )
    view = dict(views.stage_view(run, stage))
    if stage == "intelligence":
        selection = cast(
            "dict[str, Any]", dict(run.request_material).get("dataset", {})
        )
        evidence = cast("dict[str, Any]", view["evidence"])
        dataset_identity = cast(
            "dict[str, Any]", dict(run.dataset or {}).get("identity", {})
        )
        evidence["intelligence"] = source(
            "intelligence",
            asset_class=selection.get("asset_class"),
            symbol=run.symbol,
            available_at=dataset_identity.get("available_at"),
        )
        view["state"] = (
            "completed"
            if cast("Any", evidence["intelligence"])["available"]
            else "unavailable"
        )
        view["reason"] = cast("Any", evidence["intelligence"])["reason"]
    if stage == "stress":
        evidence = cast("dict[str, Any]", view["evidence"])
        stress_evidence = dict(
            cast("Mapping[str, Any]", source("stress", scenario_id=scenario_id))
        )
        stress_evidence["creation_permitted"] = "research:govern" in set(
            auth.permissions
        )
        evidence["stress"] = stress_evidence
        evidence["expectancy"] = source(
            "expectancy", profile_id=profile_id, strategy_ref=None
        )
        view["state"] = (
            "completed"
            if cast("Any", evidence["stress"])["available"]
            else "unavailable"
        )
        view["reason"] = cast("Any", evidence["stress"])["reason"]
    return view


@router.get("/runs/{run_id}/artifacts", response_model=None)
def _list_run_artifacts(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Return every safe artifact reference retained for one run.

    Args:
        run_id: Run identity.
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Artifact references carrying hash, size, and audit identity.
    """
    require_permission(auth, "research:read")
    run = _require_run(source, run_id, auth)
    return {
        "run_id": run.run_id,
        "artifacts": [dict(item) for item in run.artifacts],
        "artifact_root_owner": "api",
    }


@router.post("/runs/{run_id}/cancel", response_model=None)
def _cancel_run(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Request cooperative cancellation of one owned run.

    Args:
        run_id: Run identity.
        auth: Authenticated human principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Run detail after the cancellation request.

    Raises:
        HTTPException: If the run is unknown or owned by another principal.
    """
    require_human_permission(auth, "research:run")
    run = _registry(source).cancel_run(run_id, principal_id=auth.principal_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESEARCH_RUN_NOT_FOUND",
        )
    return views.run_detail(run)


def _frame(event: object) -> bytes:
    """Serialize one stream event as an SSE frame.

    Args:
        event: Validated stream event envelope.

    Returns:
        Encoded SSE frame.
    """
    payload = event.model_dump(mode="json")  # type: ignore[attr-defined]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return (
        f"id: {payload['sequence']}\nevent: {payload['event_type']}\n"
        f"data: {encoded}\n\n"
    ).encode()


async def _events(
    request: Request, frames: object, *, run_id: str, request_id: str
) -> AsyncIterator[bytes]:
    """Yield ordered run frames without blocking the event loop.

    The registry exposes a blocking iterator because a run executes on its own
    thread, so each advance is awaited off the loop.

    Args:
        request: Incoming request, used to detect client disconnect.
        frames: Blocking iterator of ordered run events.
        run_id: Run identity used in the stream route.
        request_id: Canonical request identifier.

    Yields:
        Encoded SSE frames until the run is terminal or the client disconnects.
    """
    iterator = iter(cast("Any", frames))
    sentinel = object()
    sequence = 0
    route = _STREAM_ROUTE.replace("{run_id}", run_id)
    while not await request.is_disconnected():
        item = await asyncio.to_thread(next, iterator, sentinel)
        if item is sentinel:
            return
        payload = dict(cast("Any", item))
        kind = str(payload.pop("kind", "progress"))
        event_type = "heartbeat" if kind == "heartbeat" else "payload"
        yield _frame(
            build_stream_event(
                sequence=sequence,
                request_id=request_id,
                route=route,
                event_type=event_type,
                payload=payload,
                cursor=str(payload.get("sequence", sequence)),
            )
        )
        sequence += 1
        if kind == "terminal":
            return


@router.get("/runs/{run_id}/events", response_class=StreamingResponse)
async def _stream_run_events(
    run_id: str,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    after: Annotated[int, Query(ge=0)] = 0,
) -> StreamingResponse:
    """Stream ordered progress for one owned run.

    Args:
        run_id: Run identity.
        request: Incoming request, used to detect client disconnect.
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.
        after: Last sequence already delivered to the caller.

    Returns:
        Authenticated server-sent-event response.

    Raises:
        HTTPException: If the run is unknown or owned by another principal.
    """
    require_permission(auth, "research:read")
    _require_run(source, run_id, auth)
    frames = _registry(source).stream_events(
        run_id, principal_id=auth.principal_id, after=after
    )
    if frames is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESEARCH_RUN_NOT_FOUND",
        )
    return StreamingResponse(
        _events(request, frames, run_id=run_id, request_id=generate_id("req")),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/automation", response_model=None, status_code=status.HTTP_202_ACCEPTED)
async def _create_automation_batch(
    request: ResearchAutomationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Queue one multi-symbol Research batch.

    Symbols are queued independently: one rejected symbol is recorded on the
    batch and does not prevent the rest from running.

    Args:
        request: Validated automation request.
        auth: Authenticated human principal.
        source: Injected Research workbench dispatcher.
        idempotency_key: Required durable replay key.

    Returns:
        Accepted batch view including per-symbol run status.
    """
    require_human_permission(auth, "research:run")
    key = _require_idempotency(idempotency_key)
    registry = _registry(source)
    experiment = _require_experiment(source, request.experiment_id, auth)

    def submit() -> object:
        """Queue the owner batch and its child runs exactly once.

        Returns:
            Accepted batch view including per-symbol run status.
        """
        batch = registry.create_batch(
            principal_id=auth.principal_id,
            experiment_id=request.experiment_id,
            symbols=request.symbols,
            trigger=request.trigger,
            reason=request.reason,
            request_material={
                "timeframe": request.timeframe,
                "preset": request.preset,
                "selected_stages": list(request.selected_stages),
                "use_cache": request.use_cache,
                "force_rerun": request.force_rerun,
                "save_artifacts": request.save_artifacts,
            },
        )
        batch_id = str(batch["batch_id"])
        runs: list[ResearchRun] = []
        for symbol in request.symbols:
            run_request = _automation_run_request(request, symbol=symbol)
            try:
                runs.append(
                    _queue_run(
                        registry=registry,
                        auth=auth,
                        experiment=experiment,
                        request=run_request,
                        symbol=symbol,
                        batch_id=batch_id,
                    )
                )
            except HTTPException as error:
                registry.record_batch_rejection(
                    batch_id,
                    symbol=symbol,
                    code="RUN_REJECTED",
                    detail=str(error.detail),
                )
        return views.batch_view(batch, runs)

    return await run_idempotent_write_async(
        principal_id=str(auth.principal_id),
        method="POST",
        route=_CREATE_AUTOMATION_ROUTE,
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: asyncio.to_thread(submit),
    )


def _automation_run_request(
    request: ResearchAutomationRequest, *, symbol: str
) -> ResearchRunCreateRequest:
    """Build one per-symbol run request from a batch request.

    Args:
        request: Validated automation request.
        symbol: Symbol this run analyzes.

    Returns:
        Safe run-create request for one symbol.
    """
    from app.services.api.widgets.research.schemas import (
        ResearchDatasetSelection,
    )
    from app.services.api.widgets.research.schemas import (
        ResearchRunCreateRequest as _RunCreate,
    )

    return _RunCreate(
        dataset=ResearchDatasetSelection(
            symbol=symbol,
            timeframe=request.timeframe,
            source_id=request.source_id,
            start=request.start,
            end=request.end,
            bar_limit=request.bar_limit,
        ),
        preset=request.preset,
        selected_stages=request.selected_stages,
        approved_overrides=request.approved_overrides,
        reason=request.reason,
        force_rerun=request.force_rerun or not request.use_cache,
        save_artifacts=request.save_artifacts,
    )


@router.get("/automation/{batch_id}", response_model=None)
def _get_automation_batch(
    batch_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
) -> object:
    """Return one owned automation batch with per-symbol progress.

    Args:
        batch_id: Batch identity.
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.

    Returns:
        Batch view including partial-failure visibility.

    Raises:
        HTTPException: If the batch is unknown or owned by another principal.
    """
    require_permission(auth, "research:read")
    registry = _registry(source)
    batch = registry.get_batch(batch_id, principal_id=auth.principal_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESEARCH_BATCH_NOT_FOUND",
        )
    runs = registry.list_runs(principal_id=auth.principal_id, batch_id=batch_id)
    return views.batch_view(batch, runs)


@router.get("/expectancy", response_model=None)
def _get_expectancy(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    profile_id: str | None = None,
    strategy_ref: str | None = None,
) -> object:
    """Return the approved expectancy profile Research governs.

    The gateway never enacts a governance transition; it reports the profile,
    its lifecycle state, and whether the caller holds the transition
    permission.

    Args:
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.
        profile_id: Optional explicit governance identity.
        strategy_ref: Optional strategy identity covered by a profile.

    Returns:
        Expectancy evidence, or an explicit unavailable state with a reason.
    """
    require_permission(auth, "research:read")
    view = dict(
        cast(
            "dict[str, Any]",
            source("expectancy", profile_id=profile_id, strategy_ref=strategy_ref),
        )
    )
    view["transition_permitted"] = "research:govern" in set(auth.permissions)
    return view


@router.post("/expectancy", response_model=None, status_code=status.HTTP_201_CREATED)
def _create_expectancy(
    request: ResearchExpectancyCreateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Create one draft expectancy profile from completed-run evidence.

    Args:
        request: Explicit measured statistics and completed run identity.
        auth: Authenticated human creator.
        source: Injected Research workbench dispatcher.
        idempotency_key: Required durable replay key.

    Returns:
        Newly persisted draft profile or its durable replay.
    """
    require_human_permission(auth, "research:govern")
    key = _require_idempotency(idempotency_key)
    request_id = generate_id("req")

    def build(*, persist: bool) -> object:
        """Build and optionally persist through Research authority.

        Returns:
            Research-owned draft profile evidence.

        Raises:
            HTTPException: If the source run is missing or incomplete.
        """
        try:
            return source(
                "build_expectancy",
                registry=_registry(source),
                principal_id=str(auth.principal_id),
                request=request,
                reviewer=str(auth.principal_id),
                request_id=request_id,
                persist=persist,
            )
        except ValueError as error:
            detail = str(error)
            status_code = (
                status.HTTP_404_NOT_FOUND
                if detail == "RESEARCH_RUN_NOT_FOUND"
                else status.HTTP_409_CONFLICT
            )
            raise HTTPException(status_code=status_code, detail=detail) from error

    preview = cast("Mapping[str, Any]", build(persist=False))
    profile_id = str(cast("Mapping[str, Any]", preview["profile"])["profile_id"])
    return run_idempotent_write(
        principal_id=str(auth.principal_id),
        method="POST",
        route=_CREATE_EXPECTANCY_ROUTE,
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=request_id,
        operation=lambda: build(persist=True),
        replay=lambda: source("expectancy", profile_id=profile_id, strategy_ref=None),
    )


@router.post(
    "/stress-scenarios", response_model=None, status_code=status.HTTP_201_CREATED
)
def _create_stress_scenario(
    request: ResearchStressScenarioCreateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Create immutable evidence from one approved reasoned scenario.

    Args:
        request: Approved scenario key and explicit hypothesis.
        auth: Authenticated human creator.
        source: Injected Research workbench dispatcher.
        idempotency_key: Required durable replay key.

    Returns:
        Newly persisted stress evidence or its durable replay.
    """
    require_human_permission(auth, "research:govern")
    key = _require_idempotency(idempotency_key)
    request_id = generate_id("req")

    def build(*, persist: bool) -> object:
        """Build and optionally persist through Research authority.

        Returns:
            Research-owned stress-scenario evidence.
        """
        return source(
            "build_stress",
            scenario_key=request.scenario_key,
            hypothesis=request.hypothesis,
            request_id=request_id,
            persist=persist,
        )

    preview = cast("Mapping[str, Any]", build(persist=False))
    scenario_id = str(cast("Mapping[str, Any]", preview["evidence"])["scenario_id"])
    return run_idempotent_write(
        principal_id=str(auth.principal_id),
        method="POST",
        route=_CREATE_STRESS_ROUTE,
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=request_id,
        operation=lambda: build(persist=True),
        replay=lambda: source("stress", scenario_id=scenario_id),
    )


@router.post("/expectancy/{profile_id}/transition", response_model=None)
def _transition_expectancy(
    profile_id: str,
    request: ResearchExpectancyTransitionRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Advance one expectancy profile through Research governance.

    Args:
        profile_id: Stable expectancy profile identity.
        request: Bounded target state and review evidence.
        auth: Authenticated human reviewer.
        source: Injected Research workbench dispatcher.
        idempotency_key: Required durable replay key.

    Returns:
        Refreshed Research-owned expectancy evidence.

    Raises:
        HTTPException: If permission, idempotency, profile identity, or the
            requested transition is invalid.
    """
    require_human_permission(auth, "research:govern")
    key = _require_idempotency(idempotency_key)
    request_id = generate_id("req")

    def transition() -> object:
        """Delegate the governed transition exactly once.

        Returns:
            Refreshed Research-owned expectancy evidence.

        Raises:
            HTTPException: If Research rejects the profile or transition.
            ValueError: If the dispatcher reports an unknown failure.
        """
        try:
            return source(
                "transition_expectancy",
                profile_id=profile_id,
                target_state=request.target_state,
                reviewer=str(auth.principal_id),
                decision=request.decision,
                reason=request.reason,
                superseded_by=request.superseded_by,
                request_id=request_id,
            )
        except ValueError as error:
            detail = str(error)
            if detail == "EXPECTANCY_PROFILE_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=detail
                ) from error
            if detail == "EXPECTANCY_TRANSITION_NOT_PERMITTED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail=detail
                ) from error
            raise

    return run_idempotent_write(
        principal_id=str(auth.principal_id),
        method="POST",
        route=_EXPECTANCY_TRANSITION_ROUTE,
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=request_id,
        operation=transition,
        replay=lambda: source("expectancy", profile_id=profile_id, strategy_ref=None),
    )


@router.get("/drift", response_model=None)
def _get_drift(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResearchSource, Depends(_research_source)],
    profile_id: str | None = None,
) -> object:
    """Return the latest performance-drift evidence Research recorded.

    A suspension proposal is advisory. The gateway reports it and never enacts
    it.

    Args:
        auth: Authenticated principal.
        source: Injected Research workbench dispatcher.
        profile_id: Optional expectancy profile identity.

    Returns:
        Drift evidence, or an explicit unavailable state with a reason.
    """
    require_permission(auth, "research:read")
    view = dict(cast("dict[str, Any]", source("drift", profile_id=profile_id)))
    view["suspension_enacted_by_ui"] = False
    return view


__all__ = ("router",)
