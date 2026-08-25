"""UI domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.ui.ports import ComposeShellPresentationCapability

if TYPE_CHECKING:
    from app.contracts.ui.ports import (
        AdministerSystemPresentationCapability,
        AuthorStrategiesPresentationCapability,
        ComposePortfoliosPresentationCapability,
        EditCodePresentationCapability,
        EditInputsPresentationCapability,
        EditProjectsPresentationCapability,
        EnsureAccessPresentationCapability,
        ExploreResultsPresentationCapability,
        ExtendViewsPresentationCapability,
        ManageDataPresentationCapability,
        ManageLayoutsPresentationCapability,
        MonitorWorkPresentationCapability,
        OperateDatabanksPresentationCapability,
        OperateTradingPresentationCapability,
        RunResearchPresentationCapability,
        StartWorkPresentationCapability,
    )

COMPOSE_SHELL_CAPABILITY: CapabilityKey[ComposeShellPresentationCapability] = (
    CapabilityKey(
        name="ui.compose-shell",
        major=1,
    )
)

START_WORK_CAPABILITY: CapabilityKey[StartWorkPresentationCapability] = CapabilityKey(
    name="ui.start-work",
    major=1,
)

MANAGE_LAYOUTS_CAPABILITY: CapabilityKey[ManageLayoutsPresentationCapability] = (
    CapabilityKey(
        name="ui.manage-layouts",
        major=1,
    )
)

EDIT_INPUTS_CAPABILITY: CapabilityKey[EditInputsPresentationCapability] = CapabilityKey(
    name="ui.edit-inputs",
    major=1,
)

AUTHOR_STRATEGIES_CAPABILITY: CapabilityKey[AuthorStrategiesPresentationCapability] = (
    CapabilityKey(
        name="ui.author-strategies",
        major=1,
    )
)

RUN_RESEARCH_CAPABILITY: CapabilityKey[RunResearchPresentationCapability] = (
    CapabilityKey(
        name="ui.run-research",
        major=1,
    )
)

EDIT_PROJECTS_CAPABILITY: CapabilityKey[EditProjectsPresentationCapability] = (
    CapabilityKey(
        name="ui.edit-projects",
        major=1,
    )
)

MANAGE_DATA_CAPABILITY: CapabilityKey[ManageDataPresentationCapability] = CapabilityKey(
    name="ui.manage-data",
    major=1,
)

OPERATE_DATABANKS_CAPABILITY: CapabilityKey[OperateDatabanksPresentationCapability] = (
    CapabilityKey(
        name="ui.operate-databanks",
        major=1,
    )
)

EXPLORE_RESULTS_CAPABILITY: CapabilityKey[ExploreResultsPresentationCapability] = (
    CapabilityKey(
        name="ui.explore-results",
        major=1,
    )
)

COMPOSE_PORTFOLIOS_CAPABILITY: CapabilityKey[
    ComposePortfoliosPresentationCapability
] = CapabilityKey(
    name="ui.compose-portfolios",
    major=1,
)

EDIT_CODE_CAPABILITY: CapabilityKey[EditCodePresentationCapability] = CapabilityKey(
    name="ui.edit-code",
    major=1,
)

MONITOR_WORK_CAPABILITY: CapabilityKey[MonitorWorkPresentationCapability] = (
    CapabilityKey(
        name="ui.monitor-work",
        major=1,
    )
)

ADMINISTER_SYSTEM_CAPABILITY: CapabilityKey[AdministerSystemPresentationCapability] = (
    CapabilityKey(
        name="ui.administer-system",
        major=1,
    )
)

OPERATE_TRADING_CAPABILITY: CapabilityKey[OperateTradingPresentationCapability] = (
    CapabilityKey(
        name="ui.operate-trading",
        major=1,
    )
)

ENSURE_ACCESS_CAPABILITY: CapabilityKey[EnsureAccessPresentationCapability] = (
    CapabilityKey(
        name="ui.ensure-access",
        major=1,
    )
)

EXTEND_VIEWS_CAPABILITY: CapabilityKey[ExtendViewsPresentationCapability] = (
    CapabilityKey(
        name="ui.extend-views",
        major=1,
    )
)
