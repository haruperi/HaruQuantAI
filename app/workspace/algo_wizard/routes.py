"""FastAPI HTTP route factory for the AlgoWizard workspace.

Description:
    Mounts the HTTP endpoints for the AlgoWizard workspace across three
    canonical servlet surfaces: /algowizard/* (WizardService and
    VisualBlockService), /constants/* (WizardCatalogueService), and
    /strategy/* (StrategyDocumentService), returning serialized
    StandardResponse[T] envelopes and mapping DomainError exceptions to
    structured HTTP 400/404/409 responses.

Purpose:
    FEAT-WIZARD-WORKSPACE: Gate G7 (Phase 5.7, WO-WZ-WORKSPACE-COORDINATOR /
    I-AppWizard) FastAPI router factory for HSL 1.0 strategy authoring,
    catalogue inspection, visual block transforms, and runtime lifecycle.

Key Capabilities:
    - FR-wizard-http-routes-algowizard: Exposes /AlgoWizard/examples/examples.json
      and /algowizard/* endpoints for examples, file load/save, Retester
      handoff, config, validation, negation, custom blocks, block groups,
      timeframe expansion, resource checks, and simulation backtests.
    - FR-wizard-http-routes-constants: Exposes /constants/* endpoints for the
      HSL block catalogue bundle, block descriptors, and commission methods.
    - FR-wizard-http-routes-strategy: Exposes /strategy/* endpoints for strategy
      registration, retrieval, listing, start, stop, status, and removal.

Python API Usage:
    from app.workspace.algo_wizard.routes import create_wizard_router

    router = create_wizard_router()

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_workspace.py --no-cov -q
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.algo_wizard.catalogue import WizardCatalogueService
from app.workspace.algo_wizard.catalogue_models import (
    GetBlockDescriptorRequest,
    GetCatalogueRequest,
    ListCommissionMethodsRequest,
)
from app.workspace.algo_wizard.strategies import StrategyDocumentService
from app.workspace.algo_wizard.strategies_models import (
    AddStrategyRequest,
    ListStrategiesRequest,
    RemoveStrategyRequest,
    StartStrategyRequest,
    StopStrategyRequest,
    StrategyIdRequest,
)
from app.workspace.algo_wizard.visual_blocks import VisualBlockService
from app.workspace.algo_wizard.visual_blocks_models import (
    AddTimeframeRequest,
    CheckResourcesRequest,
    GetWizardBacktestRequest,
    GetWizardConfigRequest,
    LoadBlockGroupsRequest,
    LoadCustomBlocksRequest,
    NegateConditionRequest,
    SaveBlockGroupsRequest,
    SaveCustomBlocksRequest,
    StopWizardBacktestRequest,
    ValidateDocumentRequest,
    WizardBacktestRequest,
)
from app.workspace.algo_wizard.workspace import WizardService
from app.workspace.algo_wizard.workspace_models import (
    ListWizardExamplesRequest,
    LoadStrategyFileRequest,
    LoadWizardExampleRequest,
    SaveStrategyFileRequest,
    SaveToRetesterRequest,
)

logger = get_logger(__name__)


def _envelope_dict(resp: StandardResponse[Any]) -> dict[str, Any]:
    """Serialize a typed StandardResponse envelope into a JSON-ready dictionary."""
    data = resp.data
    if hasattr(data, "model_dump"):
        serialized: Any = data.model_dump(mode="json")
    elif isinstance(data, tuple):
        serialized = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in data
        ]
    else:
        serialized = data
    return {
        "request_id": resp.request_id,
        "data": serialized,
        "revision": resp.revision,
    }


def _invoke_route(fn: Callable[[], StandardResponse[Any]]) -> dict[str, Any]:
    """Execute a service operation and translate DomainError into HTTPException."""
    try:
        return _envelope_dict(fn())
    except DomainError as exc:
        if exc.code.endswith("_NOT_FOUND"):
            status_code = 404
        elif "CONFLICT" in exc.code:
            status_code = 409
        else:
            status_code = 400
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        ) from exc


def _register_wizard_workspace_routes(
    router: APIRouter,
    wizard_svc: WizardService,
) -> None:
    """Mount /AlgoWizard/examples/examples.json and WizardService endpoints."""

    @router.get("/AlgoWizard/examples/examples.json")
    def get_examples_catalog(
        category: str | None = None,
        query: str | None = None,
    ) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: GET examples.json")
        req = ListWizardExamplesRequest(category=category, query=query)
        return _invoke_route(lambda: wizard_svc.list_examples(req))

    @router.post("/algowizard/examples")
    def post_examples_catalog(
        request: ListWizardExamplesRequest | None = None,
    ) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/examples")
        return _invoke_route(lambda: wizard_svc.list_examples(request))

    @router.post("/algowizard/loadExample")
    def load_example(request: LoadWizardExampleRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/loadExample")
        return _invoke_route(lambda: wizard_svc.load_example(request))

    @router.post("/algowizard/loadFile")
    def load_file(request: LoadStrategyFileRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/loadFile")
        return _invoke_route(lambda: wizard_svc.load_file(request))

    @router.post("/algowizard/saveFile")
    def save_file(request: SaveStrategyFileRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/saveFile")
        return _invoke_route(lambda: wizard_svc.save_file(request))

    @router.post("/algowizard/saveToRetester")
    def save_to_retester(request: SaveToRetesterRequest) -> dict[str, Any]:
        logger.debug(
            "FR-wizard-http-routes-algowizard: POST /algowizard/saveToRetester"
        )
        return _invoke_route(lambda: wizard_svc.save_to_retester(request))


def _register_visual_authoring_routes(
    router: APIRouter,
    visual_svc: VisualBlockService,
) -> None:
    """Mount VisualBlockService authoring and block/group endpoints."""

    @router.post("/algowizard/getConfig")
    def get_config(
        request: GetWizardConfigRequest | None = None,
    ) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/getConfig")
        return _invoke_route(lambda: visual_svc.get_config(request))

    @router.post("/algowizard/validate")
    def validate_document(request: ValidateDocumentRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/validate")
        return _invoke_route(lambda: visual_svc.validate_document(request))

    @router.post("/algowizard/negate")
    def negate_condition(request: NegateConditionRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/negate")
        return _invoke_route(lambda: visual_svc.negate_condition(request))

    @router.post("/algowizard/saveCustomBlocks")
    def save_custom_blocks(request: SaveCustomBlocksRequest) -> dict[str, Any]:
        logger.debug(
            "FR-wizard-http-routes-algowizard: POST /algowizard/saveCustomBlocks"
        )
        return _invoke_route(lambda: visual_svc.save_custom_blocks(request))

    @router.post("/algowizard/loadCustomBlocks")
    def load_custom_blocks(
        request: LoadCustomBlocksRequest | None = None,
    ) -> dict[str, Any]:
        logger.debug(
            "FR-wizard-http-routes-algowizard: POST /algowizard/loadCustomBlocks"
        )
        return _invoke_route(lambda: visual_svc.load_custom_blocks(request))

    @router.post("/algowizard/saveBlockGroups")
    def save_block_groups(request: SaveBlockGroupsRequest) -> dict[str, Any]:
        logger.debug(
            "FR-wizard-http-routes-algowizard: POST /algowizard/saveBlockGroups"
        )
        return _invoke_route(lambda: visual_svc.save_block_groups(request))

    @router.post("/algowizard/loadBlockGroups")
    def load_block_groups(
        request: LoadBlockGroupsRequest | None = None,
    ) -> dict[str, Any]:
        logger.debug(
            "FR-wizard-http-routes-algowizard: POST /algowizard/loadBlockGroups"
        )
        return _invoke_route(lambda: visual_svc.load_block_groups(request))


def _register_visual_simulation_routes(
    router: APIRouter,
    visual_svc: VisualBlockService,
) -> None:
    """Mount VisualBlockService resource, timeframe, and backtest endpoints."""

    @router.post("/algowizard/addNewTimeframe")
    def add_new_timeframe(request: AddTimeframeRequest) -> dict[str, Any]:
        logger.debug(
            "FR-wizard-http-routes-algowizard: POST /algowizard/addNewTimeframe"
        )
        return _invoke_route(lambda: visual_svc.add_timeframe(request))

    @router.post("/algowizard/checkResources")
    def check_resources(request: CheckResourcesRequest) -> dict[str, Any]:
        logger.debug(
            "FR-wizard-http-routes-algowizard: POST /algowizard/checkResources"
        )
        return _invoke_route(lambda: visual_svc.check_resources(request))

    @router.post("/algowizard/backtest")
    def run_backtest(request: WizardBacktestRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/backtest")
        return _invoke_route(lambda: visual_svc.run_backtest(request))

    @router.post("/algowizard/stopBacktest")
    def stop_backtest(request: StopWizardBacktestRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-algowizard: POST /algowizard/stopBacktest")
        return _invoke_route(lambda: visual_svc.stop_backtest(request))

    @router.post("/algowizard/backtestResults")
    def get_backtest_results(request: GetWizardBacktestRequest) -> dict[str, Any]:
        logger.debug(
            "FR-wizard-http-routes-algowizard: POST /algowizard/backtestResults"
        )
        return _invoke_route(lambda: visual_svc.get_backtest_results(request))


def _register_constants_routes(
    router: APIRouter,
    catalogue_svc: WizardCatalogueService,
) -> None:
    """Mount /constants/* endpoints on WizardCatalogueService."""

    @router.post("/constants/getAll")
    def get_all_constants(
        request: GetCatalogueRequest | None = None,
    ) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-constants: POST /constants/getAll")
        return _invoke_route(lambda: catalogue_svc.get_all(request))

    @router.post("/constants/descriptor")
    def get_block_descriptor(request: GetBlockDescriptorRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-constants: POST /constants/descriptor")
        return _invoke_route(lambda: catalogue_svc.get_block_descriptor(request))

    @router.post("/constants/commissions")
    def list_commissions(
        request: ListCommissionMethodsRequest | None = None,
    ) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-constants: POST /constants/commissions")
        return _invoke_route(lambda: catalogue_svc.list_commission_methods(request))


def _register_strategy_routes(
    router: APIRouter,
    strategy_svc: StrategyDocumentService,
) -> None:
    """Mount /strategy/* endpoints on StrategyDocumentService."""

    @router.post("/strategy/add")
    def add_strategy(request: AddStrategyRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-strategy: POST /strategy/add")
        return _invoke_route(lambda: strategy_svc.add_strategy(request))

    @router.post("/strategy/get")
    def get_strategy(request: StrategyIdRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-strategy: POST /strategy/get")
        return _invoke_route(lambda: strategy_svc.get_strategy(request))

    @router.post("/strategy/list")
    def list_strategies(
        request: ListStrategiesRequest | None = None,
    ) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-strategy: POST /strategy/list")
        return _invoke_route(lambda: strategy_svc.list_strategies(request))

    @router.post("/strategy/start")
    def start_strategy(request: StartStrategyRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-strategy: POST /strategy/start")
        return _invoke_route(lambda: strategy_svc.start_strategy(request))

    @router.post("/strategy/stop")
    def stop_strategy(request: StopStrategyRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-strategy: POST /strategy/stop")
        return _invoke_route(lambda: strategy_svc.stop_strategy(request))

    @router.post("/strategy/status")
    def get_strategy_status(request: StrategyIdRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-strategy: POST /strategy/status")
        return _invoke_route(lambda: strategy_svc.get_strategy(request))

    @router.post("/strategy/remove")
    def remove_strategy(request: RemoveStrategyRequest) -> dict[str, Any]:
        logger.debug("FR-wizard-http-routes-strategy: POST /strategy/remove")
        return _invoke_route(lambda: strategy_svc.remove_strategy(request))


def create_wizard_router(
    *,
    wizard_service: WizardService | None = None,
    catalogue_service: WizardCatalogueService | None = None,
    strategy_service: StrategyDocumentService | None = None,
    visual_block_service: VisualBlockService | None = None,
) -> APIRouter:
    """Create a FastAPI APIRouter for /algowizard/*, /constants/*, and /strategy/*."""
    svc = wizard_service or WizardService(
        catalogue_service=catalogue_service,
        strategy_service=strategy_service,
        visual_block_service=visual_block_service,
    )
    cat_svc = catalogue_service or svc.catalogue_service
    strat_svc = strategy_service or svc.strategy_service
    vis_svc = visual_block_service or svc.visual_block_service

    router = APIRouter(tags=["algo_wizard"])
    _register_wizard_workspace_routes(router, svc)
    _register_visual_authoring_routes(router, vis_svc)
    _register_visual_simulation_routes(router, vis_svc)
    _register_constants_routes(router, cat_svc)
    _register_strategy_routes(router, strat_svc)

    logger.info(
        "FR-wizard-http-routes-algowizard: mounted %d AlgoWizard routes",
        len(router.routes),
    )
    return router


wizard_router = create_wizard_router()

__all__ = [
    "create_wizard_router",
    "wizard_router",
]
