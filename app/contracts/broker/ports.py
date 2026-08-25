"""Public capability protocols (ports) for Broker capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.broker.errors import BrokerFailure
    from app.contracts.broker.models import (
        CertifyAdaptersRequest,
        CertifyAdaptersSuccess,
        ConfigureProvidersRequest,
        ConfigureProvidersSuccess,
        DeclareCapabilitiesRequest,
        DeclareCapabilitiesSuccess,
        IsolateEnvironmentsRequest,
        IsolateEnvironmentsSuccess,
        ManageSessionsRequest,
        ManageSessionsSuccess,
        ReadProviderStateRequest,
        ReadProviderStateSuccess,
        TransportOrdersRequest,
        TransportOrdersSuccess,
    )


@runtime_checkable
class DeclareCapabilitiesCapability(Protocol):
    """Capability protocol for broker capability declaration operations."""

    async def declare_capabilities(
        self,
        request: DeclareCapabilitiesRequest,
    ) -> DeclareCapabilitiesSuccess | BrokerFailure:
        """Declare provider profiles and their capability matrices.

        Args:
            request: Operation-discriminated capability declaration request.

        Returns:
            The declared provider profile or capability matrix on success,
            otherwise a structured broker failure.
        """
        ...


@runtime_checkable
class ConfigureProvidersCapability(Protocol):
    """Capability protocol for provider profile configuration operations."""

    async def configure_providers(
        self,
        request: ConfigureProvidersRequest,
    ) -> ConfigureProvidersSuccess | BrokerFailure:
        """Configure provider profiles and validate their credentials.

        Args:
            request: Operation-discriminated provider configuration request.

        Returns:
            The configured provider profile on success, otherwise a
            structured broker failure.
        """
        ...


@runtime_checkable
class IsolateEnvironmentsCapability(Protocol):
    """Capability protocol for broker environment isolation operations."""

    async def isolate_environments(
        self,
        request: IsolateEnvironmentsRequest,
    ) -> IsolateEnvironmentsSuccess | BrokerFailure:
        """Declare, verify, and resolve isolated broker environments.

        Args:
            request: Operation-discriminated environment isolation request.

        Returns:
            The declared or verified broker environment on success,
            otherwise a structured broker failure.
        """
        ...


@runtime_checkable
class ManageSessionsCapability(Protocol):
    """Capability protocol for provider session lifecycle operations."""

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Open, transition, reconnect, assess, and close fenced sessions.

        Args:
            request: Operation-discriminated session lifecycle request.

        Returns:
            The session reference, state, and readiness on success,
            otherwise a structured broker failure.
        """
        ...


@runtime_checkable
class ReadProviderStateCapability(Protocol):
    """Capability protocol for provider-truth read operations."""

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Read and normalize genuine provider account and market state.

        Args:
            request: Operation-discriminated provider-truth read request.

        Returns:
            The account snapshot, trading state, market state, or history
            page on success, otherwise a structured broker failure.
        """
        ...


@runtime_checkable
class TransportOrdersCapability(Protocol):
    """Capability protocol for authorized execution transport operations."""

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Validate, submit, cancel, modify, and journal transport requests.

        Args:
            request: Operation-discriminated execution transport request.

        Returns:
            The operation outcome, receipt, and correlation identity on
            success, otherwise a structured broker failure.
        """
        ...


@runtime_checkable
class CertifyAdaptersCapability(Protocol):
    """Capability protocol for adapter conformance and release operations."""

    async def certify_adapters(
        self,
        request: CertifyAdaptersRequest,
    ) -> CertifyAdaptersSuccess | BrokerFailure:
        """Run conformance and issue adapter and write certifications.

        Args:
            request: Operation-discriminated adapter certification request.

        Returns:
            The adapter certification or write certification on success,
            otherwise a structured broker failure.
        """
        ...
