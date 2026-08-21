"""Thread-safe registry for versioned capability providers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import TYPE_CHECKING, Any, cast

from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.scope import EffectType

if TYPE_CHECKING:
    from app.kernel.scope import FeatureScope


class CapabilityAlreadyBoundError(RuntimeError, ValueError):
    """Raised when normal registration would overwrite an active provider."""


@dataclass(frozen=True, slots=True)
class BindingToken:
    """Ownership token for one exact capability-provider generation."""

    capability: str
    owner_id: str
    generation: int


@dataclass(slots=True)
class ProviderBinding:
    """Runtime record for an active capability provider."""

    token: BindingToken
    provider: object
    registered_at: datetime


BindingInput = tuple[CapabilityKey[Any], object, str]


class ServiceRegistry:
    """Atomically publish, replace, resolve, and revoke capability bundles."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
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
        """Register one capability without overwriting an active binding.

        Returns:
            Ownership token for the new binding.
        """
        return self.register_many(
            [(capability, provider, owner_id)],
            scope=scope,
        )[0]

    def register_many(
        self,
        bindings: Sequence[BindingInput],
        scope: FeatureScope | None = None,
    ) -> list[BindingToken]:
        """Atomically register a new capability bundle.

        Returns:
            Ownership tokens in bundle order.

        Raises:
            CapabilityAlreadyBoundError: If a capability is duplicated or active.
        """
        bundle = tuple(bindings)
        self._validate_bundle(bundle, scope)
        capability_ids = tuple(capability.identifier for capability, _, _ in bundle)

        with self._lock:
            previous_generations = {
                capability_id: self._generations.get(capability_id)
                for capability_id in capability_ids
            }
            overlaps = [
                capability_id
                for capability_id in capability_ids
                if capability_id in self._bindings
            ]
            if overlaps:
                details = ", ".join(
                    f"{capability_id} -> {self._bindings[capability_id].token.owner_id}"
                    for capability_id in sorted(overlaps)
                )
                msg = (
                    "Active capability bindings cannot be overwritten by normal "
                    f"registration: {details}"
                )
                raise CapabilityAlreadyBoundError(msg)
            tokens = self._publish_bundle_locked(bundle)

        try:
            self._attach_disposers(tokens, scope)
        except Exception:
            with self._lock:
                for token in tokens:
                    active = self._bindings.get(token.capability)
                    if active is not None and active.token == token:
                        del self._bindings[token.capability]
                self._restore_generations_locked(previous_generations)
            raise
        return list(tokens)

    def replace_binding[CapT](
        self,
        capability: CapabilityKey[CapT],
        provider: CapT,
        owner_id: str,
        scope: FeatureScope | None = None,
    ) -> BindingToken:
        """Atomically replace one capability through the explicit swap path.

        Returns:
            Ownership token for the replacement binding.
        """
        return self.replace_many(
            [(capability, provider, owner_id)],
            scope=scope,
        )[0]

    def replace_many(
        self,
        bindings: Sequence[BindingInput],
        scope: FeatureScope | None = None,
    ) -> list[BindingToken]:
        """Atomically replace every capability in a provider bundle.

        Returns:
            Ownership tokens in bundle order.
        """
        bundle = tuple(bindings)
        self._validate_bundle(bundle, scope)
        capability_ids = tuple(capability.identifier for capability, _, _ in bundle)

        with self._lock:
            previous_generations = {
                capability_id: self._generations.get(capability_id)
                for capability_id in capability_ids
            }
            previous = {
                capability_id: self._bindings.get(capability_id)
                for capability_id in capability_ids
            }
            tokens = self._publish_bundle_locked(bundle)

        try:
            self._attach_disposers(tokens, scope)
        except Exception:
            with self._lock:
                for capability_id, old_binding in previous.items():
                    if old_binding is None:
                        self._bindings.pop(capability_id, None)
                    else:
                        self._bindings[capability_id] = old_binding
                self._restore_generations_locked(previous_generations)
            raise
        return list(tokens)

    def _restore_generations_locked(
        self,
        previous: dict[str, int | None],
    ) -> None:
        for capability_id, generation in previous.items():
            if generation is None:
                self._generations.pop(capability_id, None)
            else:
                self._generations[capability_id] = generation

    def _validate_bundle(
        self,
        bindings: Sequence[BindingInput],
        scope: FeatureScope | None,
    ) -> None:
        if scope is not None:
            scope.ensure_open()
        capability_ids = [
            capability.identifier for capability, _provider, _owner_id in bindings
        ]
        duplicates = sorted(
            capability_id
            for capability_id in set(capability_ids)
            if capability_ids.count(capability_id) > 1
        )
        if duplicates:
            raise CapabilityAlreadyBoundError(
                "Capability bundle contains duplicate identifiers: "
                + ", ".join(duplicates)
            )
        if any(not owner_id.strip() for _capability, _provider, owner_id in bindings):
            raise ValueError("Capability binding owner_id must not be empty")

    def _publish_bundle_locked(
        self,
        bindings: Sequence[BindingInput],
    ) -> tuple[BindingToken, ...]:
        registered_at = datetime.now(UTC)
        tokens: list[BindingToken] = []
        for capability, provider, owner_id in bindings:
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
        tokens: Sequence[BindingToken],
        scope: FeatureScope | None,
    ) -> None:
        if scope is None:
            return
        for token in tokens:
            scope.callback(
                self.revoke,
                token,
                name=f"revoke_provider:{token.capability}",
                effect_type=EffectType.SERVICE_BINDING,
            )

    def revoke(self, token: BindingToken) -> bool:
        """Revoke a binding only when its exact generation is still active.

        Returns:
            Whether the active generation was removed.
        """
        with self._lock:
            active = self._bindings.get(token.capability)
            if active is not None and active.token == token:
                del self._bindings[token.capability]
                return True
            return False

    def resolve[CapT](self, capability: CapabilityKey[CapT]) -> CapT | None:
        """Resolve an active provider for a capability.

        Returns:
            Active provider, or None when unavailable.
        """
        with self._lock:
            binding = self._bindings.get(capability.identifier)
            return cast("CapT", binding.provider) if binding is not None else None

    def require[CapT](self, capability: CapabilityKey[CapT]) -> CapT:
        """Resolve a mandatory capability or raise when unavailable.

        Returns:
            Active capability provider.

        Raises:
            CapabilityUnavailableError: If no provider is active.
        """
        provider = self.resolve(capability)
        if provider is None:
            raise CapabilityUnavailableError(capability.identifier)
        return provider

    def is_available(self, capability: CapabilityKey[Any] | str) -> bool:
        """Return whether a capability currently has an active provider."""
        capability_id = (
            capability if isinstance(capability, str) else capability.identifier
        )
        with self._lock:
            return capability_id in self._bindings

    def get_binding(self, capability_identifier: str) -> ProviderBinding | None:
        """Return the current provider binding when present."""
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
        """Clear all bindings and generation counters."""
        with self._lock:
            self._bindings.clear()
            self._generations.clear()
