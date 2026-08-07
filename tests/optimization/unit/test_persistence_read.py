"""Branch coverage for relational Optimization reads."""

import importlib

import pytest
from app.services.optimization.contracts import OptimizationError
from app.services.optimization.persistence import read


def test_unsupported_delete_module_is_explicitly_empty() -> None:
    """Load the unsupported delete module and verify its empty surface."""
    module = importlib.import_module("app.services.optimization.persistence.delete")
    assert module.__all__ == []


def test_relational_reads_handle_absence_and_invalid_payloads(mocker) -> None:
    """Return absence and fail closed on malformed stored JSON evidence."""
    row = mocker.patch.object(read, "_read_row", return_value=None)
    assert read.read_result("search-one", "req-one") is None
    assert read.read_checkpoint("search-one", "req-one") is None

    row.return_value = {"result_json": 1}
    with pytest.raises(OptimizationError, match="RESULT_PAYLOAD_INVALID"):
        read.read_result("search-one", "req-one")
    row.return_value = {"result_json": "{}"}
    with pytest.raises(OptimizationError, match="RESULT_PAYLOAD_INVALID"):
        read.read_result("search-one", "req-one")

    row.return_value = {"checkpoint_json": 1}
    with pytest.raises(OptimizationError, match="CHECKPOINT_PAYLOAD_INVALID"):
        read.read_checkpoint("search-one", "req-one")
    row.return_value = {"checkpoint_json": "{}"}
    with pytest.raises(OptimizationError, match="CHECKPOINT_PAYLOAD_INVALID"):
        read.read_checkpoint("search-one", "req-one")
