"""Tests for basic application setup."""

import pytest

from app.main import run


def test_app_run(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that app runner function runs."""
    run()
    captured = capsys.readouterr()
    assert "This is the main file" in captured.out
