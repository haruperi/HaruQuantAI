"""Unit tests for RetestValueSource normalization."""

import pytest
from app.workspace.retester.value_source import RetestValueSource


class TestRetestValueSource:
    """Test suite for RetestValueSource."""

    def test_mapping(self) -> None:
        """Assert exact mappings per RET-001 specification."""
        assert RetestValueSource.normalize("false") == "custom"
        assert RetestValueSource.normalize("true") == "strategy"
        assert RetestValueSource.normalize("custom") == "custom"
        assert RetestValueSource.normalize("strategy") == "strategy"
        assert RetestValueSource.normalize("False") == "False"
        assert RetestValueSource.normalize("") == ""
        assert RetestValueSource.normalize(None) is None

    def test_type_error(self) -> None:
        """Assert booleans and numbers raise TypeError with exact message."""
        with pytest.raises(TypeError, match="value must be str or None"):
            RetestValueSource.normalize(False)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="value must be str or None"):
            RetestValueSource.normalize(True)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="value must be str or None"):
            RetestValueSource.normalize(1)  # type: ignore[arg-type]
