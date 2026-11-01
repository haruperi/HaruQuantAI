"""Unit tests for CustomResultsPluginActionsService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.custom_results_plugin_actions import (
    CustomResultPluginActionReceipt,
    CustomResultsPluginActionsService,
)


class TestCustomResultsPluginActionsService:
    """Test suite for CustomResultsPluginActionsService."""

    def test_golden_fixture_rename_and_validation(self) -> None:
        """Verify custom plugin rename and empty title rejection."""
        service = CustomResultsPluginActionsService()
        service.register_plugin("p_1", "MyTab")

        resp = service.rename_plugin("p_1", "RiskTab")
        assert resp.data.title == "RiskTab"
        assert not resp.data.deleted

        with pytest.raises(DomainError) as exc_info:
            service.rename_plugin("p_1", "")
        assert exc_info.value.code == "RESULTS_PLUGIN_NAME_INVALID"

    def test_rename_builtin_immutable(self) -> None:
        """Verify modifying built-in plugin title raises DomainError."""
        service = CustomResultsPluginActionsService()
        with pytest.raises(DomainError) as exc_info:
            service.rename_plugin("Overview", "MyOverview")
        assert exc_info.value.code == "RESULTS_BUILTIN_PLUGIN_IMMUTABLE"

    def test_rename_conflict(self) -> None:
        """Verify conflicting title raises RESULTS_PLUGIN_NAME_CONFLICT."""
        service = CustomResultsPluginActionsService()
        service.register_plugin("p_1", "Tab1")
        service.register_plugin("p_2", "Tab2")

        with pytest.raises(DomainError) as exc_info:
            service.rename_plugin("p_1", "tab2")
        assert exc_info.value.code == "RESULTS_PLUGIN_NAME_CONFLICT"

    def test_delete_plugin(self) -> None:
        """Verify deleting custom plugin and protecting built-in plugin."""
        service = CustomResultsPluginActionsService()
        service.register_plugin("p_1", "Tab1")

        del_resp = service.delete_plugin("p_1")
        assert del_resp.data.deleted is True

        with pytest.raises(DomainError) as exc_info:
            service.delete_plugin("Equity chart")
        assert exc_info.value.code == "RESULTS_BUILTIN_PLUGIN_IMMUTABLE"

    def test_receipt_to_dict(self) -> None:
        """Verify CustomResultPluginActionReceipt to_dict."""
        receipt = CustomResultPluginActionReceipt(
            plugin_id="p1",
            title="Tab1",
            deleted=False,
            revision=2,
        )
        d = receipt.to_dict()
        assert d["plugin_id"] == "p1"
        assert d["title"] == "Tab1"
