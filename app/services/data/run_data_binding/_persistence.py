"""Persistence and binding registry for Run Data Binding."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.data.models import RunDataBinding


class RunDataBindingPersistence:
    """In-memory storage for active run data bindings."""

    def __init__(self) -> None:
        self._bindings: dict[str, RunDataBinding] = {}

    def save_binding(self, binding: RunDataBinding) -> None:
        """Store a run data binding."""
        self._bindings[binding.binding_id] = binding

    def get_binding(self, binding_id: str) -> RunDataBinding | None:
        """Retrieve a run data binding by binding ID."""
        return self._bindings.get(binding_id)

    def get_all_bindings(self) -> list[RunDataBinding]:
        """Return all stored run data bindings."""
        return list(self._bindings.values())

    def clear(self) -> None:
        """Reset storage."""
        self._bindings.clear()
