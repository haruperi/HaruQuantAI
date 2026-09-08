"""Lifecycle for selected Workspace diagnostics owner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.orchestration.capabilities import MANAGE_JOBS_CAPABILITY
from app.contracts.workspace.capabilities import ARTIFACTS_CAPABILITY, BUILD_DIAGNOSTICS_CAPABILITY
from app.services.workspace.build_diagnostics.build_diagnostics import BuildDiagnosticsService
from app.services.workspace.build_diagnostics.config import BuildDiagnosticsConfig, from_dict
from app.services.workspace.build_diagnostics.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class BuildDiagnosticsFeature:
    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        parsed = config if isinstance(config, BuildDiagnosticsConfig) else from_dict(config if isinstance(config, dict) or config is None else None)
        context.require(ARTIFACTS_CAPABILITY); context.require(MANAGE_JOBS_CAPABILITY)
        service = BuildDiagnosticsService(parsed.max_records, parsed.max_bytes)
        context.register_callback(service.close); context.provide(BUILD_DIAGNOSTICS_CAPABILITY, service)


def feature() -> BuildDiagnosticsFeature:
    return BuildDiagnosticsFeature()
