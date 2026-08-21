"""Service registry mapping versioned capabilities to active providers."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.scope import EffectType

if TYPE_CHECKING:
    from app.kernel.scope import FeatureScope


class CapabilityAlreadyBoundError(RuntimeError, ValueError):
    """Raised when attempting to register an already bound capability."""


@dataclass(frozen=True, slots=True)
class BindingToken:
    """Ownership token representing one generation of a registered provider.

    Attributes:
        capability: Formatted capability identifier string.
        owner_id: Feature identifier of the owning provider.
        generation: Monotonically increasing generation number.
    """

    capability: str
    owner_id: str
    generation: int


@dataclass(slots=True)
class ProviderBinding:
    """Runtime record of an active capability provider binding.

    Attributes:
        token: Unique ownership token with generation.
        provider: Conforming provider instance.
        registered_at: Timestamp when binding was established.
    """

    token: BindingToken
    provider: object
    registered_at: datetime


class ServiceRegistry:
    """Central registry tracking active capability providers and their lifetimes."""

    def __init__(self) -> None:
        """Initialize an empty service registry."""
        self._bindings: dict[str, ProviderBinding] = {}
        self._generations: dict[str, int] = {}

    def register[CapT](
        self,
        capability: CapabilityKey[CapT],
        provider: CapT,
        owner_id: str,
        scope: FeatureScope | None = None,
    ) -> BindingToken:
        """Register a capability provider and return its ownership token.

        Args:
            capability: Target capability key.
            provider: Implementation conforming to capability protocol.
            owner_id: Feature ID registering the provider.
            scope: Optional feature scope for unmount disposal.

        Returns:
            Ownership token representing this exact provider binding.

        Raises:
            CapabilityAlreadyBoundError: If capability is already bound.
        """
        cap_id = capability.identifier
        existing = self._bindings.get(cap_id)
        if existing is not None:
            msg = (
                f"Capability '{cap_id}' is already registered to "
                f"'{existing.token.owner_id}' "
                f"(generation {existing.token.generation}). "
                f"Overwriting an active binding requires explicit replacement."
            )
            raise CapabilityAlreadyBoundError(msg)

        current_gen = self._generations.get(cap_id, 0) + 1
        self._generations[cap_id] = current_gen

        token = BindingToken(
            capability=cap_id,
            owner_id=owner_id,
            generation=current_gen,
        )
        binding = ProviderBinding(
            token=token,
            provider=provider,
            registered_at=datetime.now(UTC),
        )
        self._bindings[cap_id] = binding

        if scope is not None:
            scope.callback(
                self.revoke,
                token,
                name=f"revoke_provider:{cap_id}",
                effect_type=EffectType.SERVICE_BINDING,
            )

        return token

    def replace_binding[CapT](
        self,
        capability: CapabilityKey[CapT],
        provider: CapT,
        owner_id: str,
        scope: FeatureScope | None = None,
    ) -> BindingToken:
        """Explicitly replace an existing capability binding with a new generation.

        Args:
            capability: Target capability key.
            provider: Implementation conforming to capability protocol.
            owner_id: Feature ID registering the replacement provider.
            scope: Optional feature scope for unmount disposal.

        Returns:
            Ownership token representing the replacement binding.
        """
        cap_id = capability.identifier
        current_gen = self._generations.get(cap_id, 0) + 1
        self._generations[cap_id] = current_gen

        token = BindingToken(
            capability=cap_id,
            owner_id=owner_id,
            generation=current_gen,
        )
        binding = ProviderBinding(
            token=token,
            provider=provider,
            registered_at=datetime.now(UTC),
        )
        self._bindings[cap_id] = binding

        if scope is not None:
            scope.callback(
                self.revoke,
                token,
                name=f"revoke_provider:{cap_id}",
                effect_type=EffectType.SERVICE_BINDING,
            )

        return token

    def register_many(
        self,
        bindings: Sequence[tuple[CapabilityKey[Any], Any, str]],
        scope: FeatureScope | None = None,
    ) -> list[BindingToken]:
        """Atomically register multiple capability bindings (all-or-nothing).

        Args:
            bindings: Sequence of (capability_key, provider_impl, owner_id) tuples.
            scope: Optional feature scope to attach unmount disposers.

        Returns:
            List of generated BindingTokens in matching order.

        Raises:
            CapabilityAlreadyBoundError: If any of the capabilities are already active.
        """
        # 1. Validation phase (verify no conflicting active bindings)
        for cap, _provider, _owner in bindings:
            cap_id = cap.identifier
            if cap_id in self._bindings:
                existing = self._bindings[cap_id]
                msg = (
                    f"Capability '{cap_id}' is already registered to "
                    f"'{existing.token.owner_id}'"
                )
                raise CapabilityAlreadyBoundError(msg)

        # 2. Registration phase
        tokens: list[BindingToken] = []
        for cap, provider, owner in bindings:
            token = self.register(cap, provider, owner, scope=scope)
            tokens.append(token)
        return tokens

    def revoke(self, token: BindingToken) -> bool:
        """Revoke a provider binding if the token matches the active generation.

        Args:
            token: Ownership token provided during registration.

        Returns:
            True if matching active binding was removed, False if token is stale.
        """
        active_binding = self._bindings.get(token.capability)
        if active_binding is not None and active_binding.token == token:
            del self._bindings[token.capability]
            return True
        return False

    def resolve[CapT](self, capability: CapabilityKey[CapT]) -> CapT | None:
        """Resolve an active provider for the given capability key.

        Args:
            capability: Target capability key.

        Returns:
            Active provider instance if available, None otherwise.
        """
        binding = self._bindings.get(capability.identifier)
        if binding is not None:
            return cast("CapT", binding.provider)
        return None

    def require[CapT](self, capability: CapabilityKey[CapT]) -> CapT:
        """Resolve a mandatory capability, raising if no provider is active.

        Args:
            capability: Target capability key.

        Returns:
            Active provider instance.

        Raises:
            CapabilityUnavailableError: If capability has no active provider.
        """
        provider = self.resolve(capability)
        if provider is None:
            raise CapabilityUnavailableError(capability.identifier)
        return provider

    def is_available(self, capability: CapabilityKey[Any] | str) -> bool:
        """Check if an active provider is registered for a capability.

        Args:
            capability: Capability key or formatted string identifier.

        Returns:
            True if an active provider exists, False otherwise.
        """
        cap_id = capability if isinstance(capability, str) else capability.identifier
        return cap_id in self._bindings

    def get_binding(self, capability_identifier: str) -> ProviderBinding | None:
        """Retrieve the active provider binding for a capability identifier.

        Args:
            capability_identifier: Formatted capability string.

        Returns:
            Active ProviderBinding if present, None otherwise.
        """
        return self._bindings.get(capability_identifier)

    def active_capabilities(self) -> dict[str, BindingToken]:
        """Return a snapshot map of all active capability identifiers to tokens.

        Returns:
            Dictionary mapping capability identifiers to active BindingTokens.
        """
        return {cap_id: binding.token for cap_id, binding in self._bindings.items()}

    def clear(self) -> None:
        """Clear all active bindings and generation counters."""
        self._bindings.clear()
        self._generations.clear()
