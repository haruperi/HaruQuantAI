"""Placeholder test to satisfy pytest discovery and import app packages."""

import app.agentic
import app.services
import app.utils


def test_placeholder() -> None:
    """Verify that app packages can be imported cleanly."""
    assert app.utils is not None
    assert app.services is not None
    assert app.agentic is not None
