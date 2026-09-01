"""Fast deterministic fixtures for Simulator unit tests."""

import pytest
from app.composition.logging import BoundLogger


@pytest.fixture(autouse=True)
def _isolate_structured_logging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep unit tests independent of queued console and file logging I/O."""
    monkeypatch.setattr(BoundLogger, "_emit", lambda *_args, **_kwargs: None)
