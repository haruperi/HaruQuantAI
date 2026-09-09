"""Interfaces domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.interfaces.operate_jobs import OperateJobsCapability
    from app.contracts.interfaces.operate_settings import OperateSettingsCapability
    from app.contracts.interfaces.ports import (
        AdministerCapabilitiesCapability,
        AutomateCommandsCapability,
        EditProjectsCapability,
        ObserveMarketCatalogueCapability,
        ObserveMarketDataCapability,
        ObserveMarketReferenceCapability,
        OperateIdentityCapability,
        OperatePortfoliosCapability,
        OperateResearchCapability,
        OperateTradingCapability,
        OperateWatchlistsCapability,
        ServeApiEventsCapability,
    )

SERVE_API_EVENTS_CAPABILITY: CapabilityKey[ServeApiEventsCapability] = CapabilityKey(
    name="interfaces.serve-api-events", major=1
)
OBSERVE_MARKET_DATA_CAPABILITY: CapabilityKey[ObserveMarketDataCapability] = CapabilityKey(
    name="interfaces.observe-market-data", major=1
)
OBSERVE_MARKET_CATALOGUE_CAPABILITY: CapabilityKey[ObserveMarketCatalogueCapability] = CapabilityKey(
    name="interfaces.observe-market-catalogue", major=1
)
AUTOMATE_COMMANDS_CAPABILITY: CapabilityKey[AutomateCommandsCapability] = CapabilityKey(
    name="interfaces.automate-commands", major=1
)
OPERATE_RESEARCH_CAPABILITY: CapabilityKey[OperateResearchCapability] = CapabilityKey(
    name="interfaces.operate-research", major=1
)
EDIT_PROJECTS_CAPABILITY: CapabilityKey[EditProjectsCapability] = CapabilityKey(
    name="interfaces.edit-projects", major=1
)
OPERATE_PORTFOLIOS_CAPABILITY: CapabilityKey[OperatePortfoliosCapability] = CapabilityKey(
    name="interfaces.operate-portfolios", major=1
)
ADMINISTER_CAPABILITIES_CAPABILITY: CapabilityKey[AdministerCapabilitiesCapability] = CapabilityKey(
    name="interfaces.administer-capabilities", major=1
)
OPERATE_TRADING_CAPABILITY: CapabilityKey[OperateTradingCapability] = CapabilityKey(
    name="interfaces.operate-trading", major=1
)
OPERATE_WATCHLISTS_CAPABILITY: CapabilityKey[OperateWatchlistsCapability] = CapabilityKey(
    name="interfaces.operate-watchlists", major=1
)
OPERATE_IDENTITY_CAPABILITY: CapabilityKey[OperateIdentityCapability] = CapabilityKey(
    name="interfaces.operate-identity", major=1
)
OPERATE_SETTINGS_CAPABILITY: CapabilityKey[OperateSettingsCapability] = CapabilityKey(
    name="interfaces.operate-settings", major=1
)
OPERATE_JOBS_CAPABILITY: CapabilityKey[OperateJobsCapability] = CapabilityKey(
    name="interfaces.operate-jobs", major=1
)
OBSERVE_MARKET_REFERENCE_CAPABILITY: CapabilityKey[ObserveMarketReferenceCapability] = CapabilityKey(
    name="interfaces.observe-market-reference", major=1
)
