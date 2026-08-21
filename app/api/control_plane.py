"""Transport-neutral liveness, readiness, and composition diagnostics."""

from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from app.api.system import SystemAPI

if TYPE_CHECKING:
    from app.composition.engine import CompositionEngine


class SystemControlPlane:
    """Expose machine-readable runtime diagnostics without binding to HTTP yet."""

    def __init__(self, engine: CompositionEngine) -> None:
        self._engine = engine
        self._system = SystemAPI(engine.registry, engine)

    def liveness(self) -> dict[str, Any]:
        """Return kernel-process liveness independent of profile readiness."""
        return {"live": True, "status": "OK"}

    def readiness(self) -> dict[str, Any]:
        """Return fail-closed readiness for the active deployment profile."""
        status = self._engine.get_status()
        return {
            "ready": status.is_ready,
            "status": "READY" if status.is_ready else "DEGRADED",
            "profile": status.profile,
            "missing_capabilities": list(status.missing_profile_capabilities),
        }

    def capabilities(self) -> dict[str, dict[str, Any]]:
        """Return active capability provider metadata."""
        return {
            identifier: asdict(info)
            for identifier, info in self._system.list_capabilities().items()
        }

    def features(self) -> dict[str, dict[str, Any]]:
        """Return configured feature lifecycle and diagnostic state."""
        runtime = self._engine.get_status()
        result: dict[str, dict[str, Any]] = {}
        for feature_id, state in runtime.feature_states.items():
            diagnostic = self._system.inspect_feature(feature_id)
            result[feature_id] = {
                "state": state.value,
                "active": diagnostic.is_active,
                "package_error": diagnostic.package_error,
                "capability_error": diagnostic.capability_error,
            }
        return result
