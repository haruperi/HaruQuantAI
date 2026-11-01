"""Unit tests for SettingsWhatToRetestService."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.retester.settings_what_to_retest import (
    SettingsWhatToRetestService,
    WhatToRetestSettings,
)


class TestSettingsWhatToRetest:
    """Test suite for WhatToRetestSettings and its service."""

    def test_resolve_keys_all_when_none(self) -> None:
        """Assert selected_keys=None resolves all databank keys."""
        settings = WhatToRetestSettings(selected_keys=None)
        keys = ("s1", "s2", "s3")
        assert SettingsWhatToRetestService.resolve_keys(settings, keys) == keys

    def test_resolve_keys_empty_when_empty_tuple(self) -> None:
        """Assert selected_keys=() resolves empty tuple without fallback."""
        settings = WhatToRetestSettings(selected_keys=())
        keys = ("s1", "s2", "s3")
        assert SettingsWhatToRetestService.resolve_keys(settings, keys) == ()

    def test_resolve_keys_explicit(self) -> None:
        """Assert explicit keys are preserved."""
        settings = WhatToRetestSettings(selected_keys=("s2",))
        keys = ("s1", "s2", "s3")
        assert SettingsWhatToRetestService.resolve_keys(settings, keys) == ("s2",)

    def test_empty_databank_raises_domain_error(self) -> None:
        """Assert empty source or target databank raises RETESTER_DATABANK_REQUIRED."""
        with pytest.raises(DomainError) as exc_info:
            SettingsWhatToRetestService.resolve_keys(
                WhatToRetestSettings(source_databank="   "),
                ("s1",),
            )
        assert exc_info.value.code == "RETESTER_DATABANK_REQUIRED"

        with pytest.raises(DomainError) as exc_info2:
            SettingsWhatToRetestService.resolve_keys(
                WhatToRetestSettings(target_databank=""),
                ("s1",),
            )
        assert exc_info2.value.code == "RETESTER_DATABANK_REQUIRED"

    def test_to_dict(self) -> None:
        """Assert to_dict serialization."""
        settings = WhatToRetestSettings(selected_keys=("s1",))
        d = settings.to_dict()
        assert d["source_databank"] == "Results"
        assert d["selected_keys"] == ["s1"]
        assert d["dismiss_failed"] is False
