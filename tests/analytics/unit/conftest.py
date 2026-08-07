"""Fast, isolated unit-test logging for Analytics."""

import pytest
from app.utils.logging.logger import BoundLogger


@pytest.fixture(autouse=True)
def _isolate_logger_emission(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Avoid queued console/file I/O while preserving semantic logger calls."""
    if request.node.path.name == "test_observability.py":
        return

    def no_op(*args: object, **kwargs: object) -> None:
        del args, kwargs

    monkeypatch.setattr(BoundLogger, "_emit", no_op)
