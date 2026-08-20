"""Provider component activation and deactivation lifecycle coordinator.

Traces to: P5-T03, Gate G5
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from app.kernel.effects import EffectScope
from app.kernel.errors import LifecycleError
from app.kernel.identifiers import CapabilityId, ProviderId
from app.kernel.manifests import ProviderManifest
from app.kernel.states import ComponentState, transition_component


class ProviderFactory(Protocol):
    """Protocol for provider factory callables."""

    def __call__(
        self,
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> object:
        """Instantiate a provider instance with injected dependencies and scope.

        Args:
            dependencies: Map of required capability IDs to initialized instances.
            config: Read-only provider configuration dictionary.
            scope: EffectScope owning reversible resources for this component.

        Returns:
            Instantiated provider instance.
        """
        ...


@dataclass(frozen=True, slots=True)
class ActiveComponent:
    """Immutable representation of an active, initialized provider component."""

    provider_id: ProviderId
    generation_id: UUID
    state: ComponentState
    instance: object
    scope: EffectScope


def activate_component(
    *,
    manifest: ProviderManifest,
    factory: ProviderFactory,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> ActiveComponent:
    """Activate a provider component through the lifecycle state machine.

    Args:
        manifest: Provider manifest metadata.
        factory: Provider factory callable.
        dependencies: Read-only mapping of capability dependencies.
        config: Configuration dictionary for the provider.
        scope: EffectScope to manage resource cleanup.

    Returns:
        ActiveComponent instance in ACTIVE state.

    Raises:
        LifecycleError: If component activation fails or scope fails cleanup.
    """
    gen_id = uuid4()
    state = ComponentState.DISCOVERED
    state = transition_component(state, ComponentState.RESOLVING)
    state = transition_component(state, ComponentState.STARTING)

    try:
        instance = factory(
            dependencies=dependencies,
            config=config,
            scope=scope,
        )
    except Exception as exc:
        try:
            scope.close()
        except Exception:
            transition_component(state, ComponentState.FAILED_CLEANUP)
            raise
        transition_component(state, ComponentState.FAILED)
        raise LifecycleError(
            f"provider activation failed: {manifest.provider_id}"
        ) from exc

    state = transition_component(state, ComponentState.ACTIVE)

    return ActiveComponent(
        provider_id=manifest.provider_id,
        generation_id=gen_id,
        state=state,
        instance=instance,
        scope=scope,
    )


def deactivate_component(
    component: ActiveComponent,
    *,
    timeout_seconds: float = 30.0,
) -> None:
    """Deactivate a component and unwind its effect scope resources in reverse order.

    Args:
        component: ActiveComponent to deactivate.
        timeout_seconds: Maximum allowed time for drain and stop (> 0).

    Raises:
        ValueError: If timeout_seconds is <= 0.
        LifecycleError: If state transition or scope cleanup fails.
    """
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be > 0")

    if component.scope.closed:
        return

    state = component.state
    state = transition_component(state, ComponentState.DRAINING)
    state = transition_component(state, ComponentState.STOPPING)

    try:
        component.scope.close()
    except Exception:
        transition_component(state, ComponentState.FAILED_CLEANUP)
        raise

    transition_component(state, ComponentState.STOPPED)


__all__ = (
    "ActiveComponent",
    "ProviderFactory",
    "activate_component",
    "deactivate_component",
)
