"""Research workbench gateway feature (FEAT-API-26)."""

from app.services.api.workstation.research.orchestration import (
    build_research_executor,
    build_research_registry,
    build_research_runtime_context,
    build_research_source,
    capture_artifact_auth,
)
from app.services.api.workstation.research.presets import (
    build_preset_config,
    get_stage_vocabulary,
    list_research_presets,
    resolve_selected_stages,
)
from app.services.api.workstation.research.projections import STAGE_VIEWS

__all__ = (
    "STAGE_VIEWS",
    "build_preset_config",
    "build_research_executor",
    "build_research_registry",
    "build_research_runtime_context",
    "build_research_source",
    "capture_artifact_auth",
    "get_stage_vocabulary",
    "list_research_presets",
    "resolve_selected_stages",
)
