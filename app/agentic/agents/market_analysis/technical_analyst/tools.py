"""Governed evidence tools for the Technical Analyst.

A tool here is a narrow typed adapter to one public deterministic operation. It
contains no model, no hidden business policy, no provider object, and no
alternate calculation: it asks Data and Indicators for what they already
computed and bounds the answer.

Every call routes through `authorize_tool_call` **before** invocation, so a
disabled tool, an ineligible role, a scope mismatch, or an exhausted budget
stops the call rather than being detected afterwards. A denied call returns a
typed denial; it never falls through to the receiver.

Receiver operations arrive as an injected port. Production composition binds
the real `app.services.data` and `app.services.indicators` package-root
functions; tests bind deterministic doubles. Agentic itself opens no
connection and holds no credential.

**Outstanding:** durable budget reservation and the redacted call-start and
call-outcome telemetry described by `docs/dev/agentic_firm/11_tool_standard.md`
belong to `FEAT-AGT-21` operations, which is `Missing`. Audit evidence is
recorded through the `context_memory` audit store in the meantime.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.context_memory.repository import store_memory
from app.agentic.permissions.authorization import (
    ToolCallOutcome,
    call_governed_tool,
)
from app.composition.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.governance.models import FirmMandate
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy

logger = get_logger(__name__)

# The registered tool identities this role may request. Each maps to exactly
# one public receiver operation.
MARKET_DATA_TOOL = "data.get_market_data"
QUALITY_TOOL = "data.inspect_data_quality"
SESSION_TOOL = "data.get_market_hours"
INDICATOR_TOOL = "indicators.get_indicator_result_metadata"


@runtime_checkable
class TechnicalEvidencePort(Protocol):
    """Read-only access to the canonical evidence this role interprets."""

    def fetch_market_evidence(
        self,
        instrument: str,
        timeframe: str,
    ) -> Mapping[str, str]:
        """Return canonical market evidence for one instrument and timeframe.

        Args:
            instrument: Canonical instrument identity.
            timeframe: Canonical timeframe.

        Returns:
            Bounded canonical market evidence.
        """
        ...

    def fetch_quality_evidence(self, instrument: str) -> Mapping[str, str]:
        """Return canonical data-quality evidence for one instrument.

        Args:
            instrument: Canonical instrument identity.

        Returns:
            Bounded quality evidence.
        """
        ...

    def fetch_session_evidence(self, instrument: str) -> Mapping[str, str]:
        """Return canonical session and market-hours evidence.

        Args:
            instrument: Canonical instrument identity.

        Returns:
            Bounded session evidence.
        """
        ...

    def fetch_indicator_versions(
        self,
        indicators: tuple[str, ...],
    ) -> Mapping[str, str]:
        """Return the exact registered version of each requested indicator.

        Args:
            indicators: Requested registered indicator names.

        Returns:
            Indicator name to exact registered version.
        """
        ...


def call_evidence_tool(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool: ToolPolicy,
    principal_id: str,
    task_id: str,
    request_scope: Mapping[str, str],
    receiver_call: Callable[[], Mapping[str, object]],
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    calls_used: int = 0,
) -> ToolCallOutcome:
    """Authorize and perform one governed evidence tool call.

    Delegates enforcement to the shared `call_governed_tool` wrapper owned by
    `FEAT-AGT-05` and supplies this feature's audit sink, so `permissions/`
    stays free of a `context_memory/` dependency.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool: Registered tool policy.
        principal_id: Authenticated requesting principal.
        task_id: Owning task identity.
        request_scope: Scope declared for this call.
        receiver_call: Zero-argument callable invoking the receiver operation.
        at_time: Call time.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        calls_used: Tool invocations already consumed by this task.

    Returns:
        The bounded outcome, denied or completed.
    """

    def audit_hook(tool_name: str, outcome: str) -> None:
        """Record one redacted tool-call audit entry.

        Args:
            tool_name: Tool identity invoked.
            outcome: Enumerated call outcome.
        """
        if audit_store is None:
            return
        # The ordinal keeps two calls to the same tool in the same instant
        # distinguishable; without it they would share a content identity.
        store_memory(
            audit_store,
            "audit",
            task_id,
            policy.role_id,
            {
                "tool": tool_name,
                "outcome": outcome,
                "call": str(calls_used + 1),
            },
            {"environment": "sandbox"},
            "audit-730d",
            at_time=at_time,
        )

    return call_governed_tool(
        mandate,
        policy,
        tool,
        principal_id,
        task_id,
        request_scope,
        receiver_call,
        at_time,
        nonce_store=nonce_store,
        audit_hook=audit_hook,
        calls_used=calls_used,
    )


@runtime_checkable
class _MarketEvidenceReader(Protocol):
    """The Data-side operations the composition root supplies."""

    def fetch_market_evidence(
        self,
        instrument: str,
        timeframe: str,
    ) -> Mapping[str, str]:
        """Return canonical market evidence.

        Args:
            instrument: Canonical instrument identity.
            timeframe: Canonical timeframe.

        Returns:
            Bounded canonical market evidence.
        """
        ...

    def fetch_quality_evidence(self, instrument: str) -> Mapping[str, str]:
        """Return canonical data-quality evidence.

        Args:
            instrument: Canonical instrument identity.

        Returns:
            Bounded quality evidence.
        """
        ...

    def fetch_session_evidence(self, instrument: str) -> Mapping[str, str]:
        """Return canonical session evidence.

        Args:
            instrument: Canonical instrument identity.

        Returns:
            Bounded session evidence.
        """
        ...


@runtime_checkable
class _IndicatorReader(Protocol):
    """The Indicators-side operation the composition root supplies."""

    def fetch_indicator_versions(
        self,
        indicators: tuple[str, ...],
    ) -> Mapping[str, str]:
        """Return the exact registered indicator versions.

        Args:
            indicators: Requested registered indicator names.

        Returns:
            Indicator name to exact registered version.
        """
        ...


class _PackageRootEvidencePort:
    """Binds the real Data and Indicators package-root public operations.

    Constructed only by an approved composition root. It performs read-only
    calls through documented public APIs and never touches a provider SDK, a
    credential, or a broker.
    """

    def __init__(
        self,
        market_reader: _MarketEvidenceReader,
        indicator_reader: _IndicatorReader,
    ) -> None:
        """Store the injected receiver-domain callables.

        Args:
            market_reader: Data package-root retrieval facade.
            indicator_reader: Indicators package-root facade.
        """
        self._market_reader = market_reader
        self._indicator_reader = indicator_reader

    def fetch_market_evidence(
        self,
        instrument: str,
        timeframe: str,
    ) -> Mapping[str, str]:
        """Return canonical market evidence.

        Args:
            instrument: Canonical instrument identity.
            timeframe: Canonical timeframe.

        Returns:
            Bounded canonical market evidence.
        """
        return self._market_reader.fetch_market_evidence(instrument, timeframe)

    def fetch_quality_evidence(self, instrument: str) -> Mapping[str, str]:
        """Return canonical data-quality evidence.

        Args:
            instrument: Canonical instrument identity.

        Returns:
            Bounded quality evidence.
        """
        return self._market_reader.fetch_quality_evidence(instrument)

    def fetch_session_evidence(self, instrument: str) -> Mapping[str, str]:
        """Return canonical session evidence.

        Args:
            instrument: Canonical instrument identity.

        Returns:
            Bounded session evidence.
        """
        return self._market_reader.fetch_session_evidence(instrument)

    def fetch_indicator_versions(
        self,
        indicators: tuple[str, ...],
    ) -> Mapping[str, str]:
        """Return the exact registered indicator versions.

        Args:
            indicators: Requested registered indicator names.

        Returns:
            Indicator name to exact registered version.
        """
        return self._indicator_reader.fetch_indicator_versions(indicators)


def build_package_root_evidence_port(
    market_reader: _MarketEvidenceReader,
    indicator_reader: _IndicatorReader,
) -> TechnicalEvidencePort:
    """Build the evidence port bound to receiver-domain public operations.

    Args:
        market_reader: Data package-root retrieval facade.
        indicator_reader: Indicators package-root facade.

    Returns:
        A port satisfying `TechnicalEvidencePort`.
    """
    logger.debug("Building the technical-analyst evidence port")
    return _PackageRootEvidencePort(market_reader, indicator_reader)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered tool identities.
    """
    return (INDICATOR_TOOL, MARKET_DATA_TOOL, QUALITY_TOOL, SESSION_TOOL)
