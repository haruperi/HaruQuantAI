"""Interfaces domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.interfaces.ports import (
        AdministerCapabilitiesCapability,
        AutomateCommandsCapability,
        EditProjectsCapability,
        ObserveMarketDataCapability,
        OperatePortfoliosCapability,
        OperateResearchCapability,
        OperateTradingCapability,
        ServeApiEventsCapability,
    )

SERVE_API_EVENTS_CAPABILITY: CapabilityKey[ServeApiEventsCapability] = CapabilityKey(
    name="interfaces.serve-api-events",
    major=1,
)

OBSERVE_MARKET_DATA_CAPABILITY: CapabilityKey[ObserveMarketDataCapability] = (
    CapabilityKey(
        name="interfaces.observe-market-data",
        major=1,
    )
)

AUTOMATE_COMMANDS_CAPABILITY: CapabilityKey[AutomateCommandsCapability] = CapabilityKey(
    name="interfaces.automate-commands",
    major=1,
)

OPERATE_RESEARCH_CAPABILITY: CapabilityKey[OperateResearchCapability] = CapabilityKey(
    name="interfaces.operate-research",
    major=1,
)

EDIT_PROJECTS_CAPABILITY: CapabilityKey[EditProjectsCapability] = CapabilityKey(
    name="interfaces.edit-projects",
    major=1,
)

OPERATE_PORTFOLIOS_CAPABILITY: CapabilityKey[OperatePortfoliosCapability] = (
    CapabilityKey(
        name="interfaces.operate-portfolios",
        major=1,
    )
)

ADMINISTER_CAPABILITIES_CAPABILITY: CapabilityKey[AdministerCapabilitiesCapability] = (
    CapabilityKey(
        name="interfaces.administer-capabilities",
        major=1,
    )
)

OPERATE_TRADING_CAPABILITY: CapabilityKey[OperateTradingCapability] = CapabilityKey(
    name="interfaces.operate-trading",
    major=1,
)
