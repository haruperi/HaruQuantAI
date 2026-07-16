"""Unit tests for handle-free storage contracts."""

from pathlib import Path

import pytest
from app.services.data.contracts import (
    DatasetLoadRequest,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.contracts.errors import DataError


def test_storage_contracts_are_bounded_and_handle_free() -> None:
    """Storage inputs cannot represent traversal or a live connection."""
    with pytest.raises(DataError):
        DatasetLoadRequest(
            relative_path=Path("C:/private/data.parquet"),
            format="parquet",
            request_id="req-55534494e3e251376fd807770b971def888ed55d5e2a9584b51e04bebc77a554",
        )
    with pytest.raises(DataError):
        StatementPlan(statements=("SELECT 1",), parameter_sets=(), max_rows=1)
    assert "connection" not in TransactionRequest.model_fields
