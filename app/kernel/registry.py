"""Thread-safe service registry mapping versioned capabilities to active providers."""

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import TYPE_CHECKING, Any, cast

from app.kernel.capability import CapabilityKey, CapabilityUnavailableError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.kernel.scope import FeatureScope


class ActiveBindingError(RuntimeError):
    """Raised when normal registration would overwrite an active provider."""


@dataclass(frozen=True, slots=True)
class BindingToken:
    """Ownership token representing one generation of a capability provider."""

    capability: str
    owner_id: str
    generation: int


@dataclass(slots=True)
class ProviderBinding:
    """Runtime record of one active capability provider binding."""

    token: BindingToken
    provider: object
    registered_at: datetime


class ServiceRegistry:
    """Central registry with atomic publication and generation-safe revocation."""

    def __init__(self) -> None:
        self._bindings: dict[str, ProviderBinding] = {}
        self._generations: dict[str, int] = {}
        self._lock = RLock()

    def register[CapT](
        self,
        capability: CapabilityKey[CapT],
        provider: CapT,
        owner_id: str,
        scope: FeatureScope | None = None,
    ) -> BindingToken:
        """Register one provider without replacing an active binding."""
        tokens = self.register_many(
            ((capability, provider),),
            owner_id=owner_id,
            scope=scope,
        )
        return tokens[0]

    def register_many(
        self,
        providers: Sequence[tuple[CapabilityKey[Any], object]],
        *,
        owner_id: str,
        scope: FeatureScope | None = None,
    ) -> tuple[BindingToken, ...]:
        """Publish a new capability bundle atomically; reject active overlaps."""
        provider_tuple = tuple(providers)
        capability_ids = tuple(capability.identifier for capability, _ in provider_tuple)
        if len(set(capability_ids)) != len(capability_ids):
            raise ActiveBindingError("Capability bundle contains duplicate identifiers")

        with self._lock:
            overlaps = [
                capability_id
                for capability_id in capability_ids
                if capability_id in self._bindings
            ]
            if overlaps:
                raise ActiveBindingError(
                    "Active capability bindings cannot be overwritten by normal "
                    f"registration: {', '.join(sorted(overlaps))}"
                )
            tokens = self._publish_locked(provider_tuple, owner_id=owner_id)

        self._attach_disposers(tokens, scope)
        return tokens

    def replace_many(
        self,
        providers: Sequence[tuple[CapabilityKey[Any], object]],
        *,
        owner_id: str,
        scope: FeatureScope | None = None,
    ) -> tuple[BindingToken, ...]:
        """Atomically replace a capability bundle through the explicit swap path."""
        provider_tuple = tuple(providers)
        capability_ids = tuple(capability.identifier for capability, _ in provider_tuple)
        if len(set(capability_ids)) != len(capability_ids):
            raise ActiveBindingError("Replacement bundle contains duplicate identifiers")
        with self._lock:
            tokens = self._publish_locked(provider_tuple, owner_id=owner_id)
        self._attach_disposers(tokens, scope)
        return tokens

    def _publish_locked(
        self,
        providers: Sequence[tuple[CapabilityKey[Any], object]],
        *,
        owner_id: str,
    ) -> tuple[BindingToken, ...]:
        """Publish providers while the registry lock is already held."""
        registered_at = datetime.now(UTC)
        tokens: list[BindingToken] = []
        for capability, provider in providers:
            capability_id = capability.identifier
            generation = self._generations.get(capability_id, 0) + 1
            self._generations[capability_id] = generation
            token = BindingToken(
                capability=capability_id,
                owner_id=owner_id,
                generation=generation,
            )
            self._bindings[capability_id] = ProviderBinding(
                token=token,
                provider=provider,
                registered_at=registered_at,
            )
            tokens.append(token)
        return tuple(tokens)

    def _attach_disposers(
        self,
        tokens: tuple[BindingToken, ...],
        scope: FeatureScope | None,
    ) -> None:
        if scope is None:
            return
        for token in tokens:
            scope.callback(
                self.revoke,
                token,
                name=f"revoke_provider:{token.capability}",
            )

    def revoke(self, token: BindingToken) -> bool:
        """Revoke a binding only when the exact active generation matches."""
        with self._lock:
            active_binding = self._bindings.get(token.capability)
            if active_binding is not None and active_binding.token == token:
                del self._bindings[token.capability]
                return True
            return False

    def resolve[CapT](self, capability: CapabilityKey[CapT]) -> CapT | None:
        """Resolve an active provider for a capability."""
        with self._lock:
            binding = self._bindings.get(capability.identifier)
            return cast("CapT", binding.provider) if binding is not None else None

    def require[CapT](self, capability: CapabilityKey[CapT]) -> CapT:
        """Resolve a mandatory capability or raise CapabilityUnavailableError."""
        provider = self.resolve(capability)
        if provider is None:
            raise CapabilityUnavailableError(capability.identifier)
        return provider

    def is_available(self, capability: CapabilityKey[Any] | str) -> bool:
        """Return whether an active provider exists."""
        capability_id = (
            capability if isinstance(capability, str) else capability.identifier
        )
        with self._lock:
            return capability_id in self._bindings

    def get_binding(self, capability_identifier: str) -> ProviderBinding | None:
        """Return the current binding when present."""
        with self._lock:
            return self._bindings.get(capability_identifier)

    def active_capabilities(self) -> dict[str, BindingToken]:
        """Return a snapshot of active capability ownership tokens."""
        with self._lock:
            return {
                capability_id: binding.token
                for capability_id, binding in self._bindings.items()
            }

    def clear(self) -> None:
        """Clear active bindings and generation counters."""
        with self._lock:
            self._bindings.clear()
            self._generations.clear()
