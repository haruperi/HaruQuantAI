"""Custom results plugin tab rename and deletion service.

Description:
    Implements CustomResultsPluginActionsService managing rename and deletion
    lifecycle for custom user-authored results plugins while enforcing naming
    validations and immutability of built-in system plugin tabs.

Purpose:
    FEAT-RESULTS-CUSTOM-PLUGIN-ACTIONS: Custom results plugin actions.

Key Capabilities:
    - FR-results-custom-plugin-actions: Rename and delete custom plugin tabs.

Python API Usage:
    from app.workspace.results.custom_results_plugin_actions import (
        CustomResultsPluginActionsService,
    )
    service = CustomResultsPluginActionsService()
    receipt = service.rename_plugin("tab_1", "RiskTab")

CLI Usage:
    python -m app.cli results plugins rename --plugin-id tab_1 --title RiskTab
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.results.app_results import wrap_response

logger = get_logger(__name__)

MAX_TITLE_LENGTH = 64
BUILTIN_PLUGIN_TITLES = frozenset(
    {
        "Overview",
        "List of trades",
        "Equity chart",
        "Trade analysis",
        "Source code",
    }
)


@dataclass(frozen=True, slots=True)
class CustomResultPluginActionReceipt:
    """Receipt for custom plugin rename or deletion."""

    plugin_id: str
    title: str
    deleted: bool
    revision: int

    def to_dict(self) -> dict[str, Any]:
        """Convert receipt to dictionary representation."""
        return {
            "plugin_id": self.plugin_id,
            "title": self.title,
            "deleted": self.deleted,
            "revision": self.revision,
        }


class CustomResultsPluginActionsService:
    """Service handling rename and delete operations for custom results plugins."""

    def __init__(self) -> None:
        """Initialize service with in-memory plugin registry."""
        self._plugins: dict[str, str] = {}  # plugin_id -> title
        self._revision: int = 1

    def register_plugin(self, plugin_id: str, title: str) -> None:
        """Register a custom plugin for management."""
        self._plugins[plugin_id] = title

    def rename_plugin(
        self, plugin_id: str, new_title: str
    ) -> StandardResponse[CustomResultPluginActionReceipt]:
        """Rename custom plugin tab validating title constraints."""
        stripped = new_title.strip()
        if not stripped or len(stripped) > MAX_TITLE_LENGTH:
            raise DomainError(
                code="RESULTS_PLUGIN_NAME_INVALID",
                message=(
                    f"Plugin title must be between 1 and {MAX_TITLE_LENGTH} characters"
                ),
                details={"title": new_title},
            )

        if plugin_id in BUILTIN_PLUGIN_TITLES or stripped in BUILTIN_PLUGIN_TITLES:
            raise DomainError(
                code="RESULTS_BUILTIN_PLUGIN_IMMUTABLE",
                message=f"Built-in plugin '{plugin_id}' cannot be modified",
                details={"plugin_id": plugin_id},
            )

        # Check case-insensitive collision
        lower_new = stripped.lower()
        for pid, existing_title in self._plugins.items():
            if pid != plugin_id and existing_title.lower() == lower_new:
                raise DomainError(
                    code="RESULTS_PLUGIN_NAME_CONFLICT",
                    message=(
                        f"Plugin title '{stripped}' conflicts with "
                        f"existing plugin '{pid}'"
                    ),
                    details={"title": stripped, "conflicting_plugin_id": pid},
                )

        self._plugins[plugin_id] = stripped
        self._revision += 1

        logger.info(
            "FR-results-custom-plugin-actions: renamed plugin %s to '%s'",
            plugin_id,
            stripped,
        )
        receipt = CustomResultPluginActionReceipt(
            plugin_id=plugin_id,
            title=stripped,
            deleted=False,
            revision=self._revision,
        )
        return wrap_response(
            request_id=f"req_{plugin_id}_rename",
            data=receipt,
            json_payload=receipt.to_dict(),
            revision=self._revision,
        )

    def delete_plugin(
        self, plugin_id: str
    ) -> StandardResponse[CustomResultPluginActionReceipt]:
        """Delete custom plugin tab, protecting built-in plugins."""
        if plugin_id in BUILTIN_PLUGIN_TITLES:
            raise DomainError(
                code="RESULTS_BUILTIN_PLUGIN_IMMUTABLE",
                message=f"Built-in plugin '{plugin_id}' cannot be deleted",
                details={"plugin_id": plugin_id},
            )

        title = self._plugins.pop(plugin_id, plugin_id)
        self._revision += 1

        logger.info(
            "FR-results-custom-plugin-actions: deleted plugin %s",
            plugin_id,
        )
        receipt = CustomResultPluginActionReceipt(
            plugin_id=plugin_id,
            title=title,
            deleted=True,
            revision=self._revision,
        )
        return wrap_response(
            request_id=f"req_{plugin_id}_delete",
            data=receipt,
            json_payload=receipt.to_dict(),
            revision=self._revision,
        )
