"""Controlled synchronous Tier-1 configuration replacement controller.

Traces to: P17-T01, Phase 17, Gate G17
"""

# ruff: noqa: E402
from __future__ import annotations

import datetime as dt
import sys
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.composition.reconciliation import (
    ProviderConfiguration,
    reconcile_configuration,
)
from app.kernel.identifiers import ProviderId
from app.utils.logging import get_logger

if TYPE_CHECKING:
    from app.composition.runtime import CompositionRuntime
    from app.kernel.lifecycle import ProviderFactory
    from app.kernel.registry import ProviderInventory

_logger = get_logger("app.composition.controller")
_CONTROLLER_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class ConfigurationReplacementEvidence:
    """Bounded, secret-safe audit record of a configuration replacement execution."""

    request_id: str
    changed_provider_ids: tuple[str, ...]
    previous_generation_ids: tuple[str, ...]
    active_generation_ids: tuple[str, ...]
    rolled_back: bool
    completed_at: str


def replace_provider_configuration(
    runtime: CompositionRuntime,
    inventory: ProviderInventory,
    current: ProviderConfiguration,
    candidate: ProviderConfiguration,
    *,
    factories: Mapping[ProviderId, ProviderFactory],
    request_id: str,
    clock: Callable[[], dt.datetime] | None = None,
) -> ConfigurationReplacementEvidence:
    """Validate and atomically apply an installed-provider configuration replacement.

    Args:
        runtime: Active CompositionRuntime instance.
        inventory: Discovered and registered ProviderInventory.
        current: Incumbent ProviderConfiguration.
        candidate: Candidate ProviderConfiguration to apply.
        factories: Mapping of ProviderId to provider factory callable.
        request_id: Unique non-blank request identifier.
        clock: Optional UTC datetime factory callable.

    Returns:
        ConfigurationReplacementEvidence summarizing the atomic transaction.

    Raises:
        ValueError: If request_id is blank.
        ManifestValidationError: If candidate references an uninstalled provider.
        LifecycleError: If candidate fails and rollback cannot be completed.
    """
    if not request_id or not request_id.strip():
        msg = "request_id must be a non-blank string"
        raise ValueError(msg)

    with _CONTROLLER_LOCK:
        now_fn = clock or (lambda: dt.datetime.now(dt.UTC))
        prev_gens = tuple(
            str(g.generation_id) for g in runtime.pin_graph().generations.values()
        )

        _logger.info("Executing configuration replacement request %s", request_id)

        try:
            result = reconcile_configuration(
                runtime=runtime,
                inventory=inventory,
                current=current,
                candidate=candidate,
                factories=factories,
            )
            active_gens = tuple(
                str(g.generation_id) for g in runtime.pin_graph().generations.values()
            )

            if result.rolled_back:
                _logger.error(
                    "Configuration replacement request %s rolled back to incumbent",
                    request_id,
                )
            else:
                _logger.info(
                    "Configuration replacement request %s completed successfully with %d changed provider(s)",
                    request_id,
                    len(result.changed_provider_ids),
                )

            return ConfigurationReplacementEvidence(
                request_id=request_id,
                changed_provider_ids=tuple(
                    str(pid) for pid in result.changed_provider_ids
                ),
                previous_generation_ids=prev_gens,
                active_generation_ids=active_gens,
                rolled_back=result.rolled_back,
                completed_at=now_fn().isoformat(),
            )
        except Exception as exc:
            _logger.error(
                "Configuration replacement request %s failed with exception: %s",
                request_id,
                exc,
            )
            raise
