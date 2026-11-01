"""Unit tests for RetestPreflight policy."""

import pytest
from app.workspace.retester.preflight import RetestPreflight


class TestRetestPreflight:
    """Test suite for RetestPreflight."""

    def test_record_keys_selection(self) -> None:
        """Assert selection resolution per RET-002 specification."""
        databank = ("a", "b", "c")
        # None returns all keys
        assert (
            RetestPreflight.record_keys(databank_keys=databank, selected_keys=None)
            == databank
        )

        # Empty selection returns empty tuple (no silent fallback)
        assert (
            RetestPreflight.record_keys(databank_keys=databank, selected_keys=()) == ()
        )

        # Explicit selection preserves ordering and duplicates
        assert RetestPreflight.record_keys(
            databank_keys=databank,
            selected_keys=("b", "b", "a"),
        ) == ("b", "b", "a")

    def test_record_keys_type_errors(self) -> None:
        """Assert invalid types raise exact TypeError."""
        with pytest.raises(TypeError, match="record keys must be tuples of strings"):
            RetestPreflight.record_keys(databank_keys=["a", "b"], selected_keys=None)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="record keys must be tuples of strings"):
            RetestPreflight.record_keys(databank_keys=("a", 1), selected_keys=None)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="record keys must be tuples of strings"):
            RetestPreflight.record_keys(databank_keys=("a",), selected_keys=["a"])  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="record keys must be tuples of strings"):
            RetestPreflight.record_keys(databank_keys=("a",), selected_keys=("a", True))  # type: ignore[arg-type]

    def test_mode_resolution(self) -> None:
        """Assert mode 0 vs 1 per RET-002 specification."""
        # Mode 1 when disabled
        assert (
            RetestPreflight.mode(cross_checks_enabled=False, creates_subjobs=(True,))
            == 1
        )
        assert RetestPreflight.mode(cross_checks_enabled=False, creates_subjobs=()) == 1

        # Mode 0 when enabled and any subjob check enabled
        assert (
            RetestPreflight.mode(
                cross_checks_enabled=True, creates_subjobs=(False, True)
            )
            == 0
        )
        assert (
            RetestPreflight.mode(cross_checks_enabled=True, creates_subjobs=(True,))
            == 0
        )

        # Mode 1 when enabled but no subjob check creates subjobs
        assert (
            RetestPreflight.mode(
                cross_checks_enabled=True, creates_subjobs=(False, False)
            )
            == 1
        )
        assert RetestPreflight.mode(cross_checks_enabled=True, creates_subjobs=()) == 1

    def test_mode_type_errors(self) -> None:
        """Assert non-boolean arguments raise TypeError."""
        with pytest.raises(TypeError, match="cross-check mode requires booleans"):
            RetestPreflight.mode(cross_checks_enabled=1, creates_subjobs=())  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="cross-check mode requires booleans"):
            RetestPreflight.mode(cross_checks_enabled=True, creates_subjobs=[True])  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="cross-check mode requires booleans"):
            RetestPreflight.mode(cross_checks_enabled=True, creates_subjobs=(1,))  # type: ignore[arg-type]
