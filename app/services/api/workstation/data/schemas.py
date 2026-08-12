"""Data gateway request schemas."""

from collections.abc import Mapping
from typing import Literal

from app.services.api.contracts.models import _BaseApiContract


class DatasetPrepareRequest(_BaseApiContract):
    """Governed dataset preparation command.

    Preparation is a two-step owner delegation: Data fetches the requested
    market dataset and then persists it. Both request shapes belong to Data; the
    gateway forwards them and stores nothing itself.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.dataset_prepare_request.v1"] = (
        "api.dataset_prepare_request.v1"
    )
    market_request: Mapping[str, object]
    save_request: Mapping[str, object]


class DatasetImportRequest(_BaseApiContract):
    """Governed external dataset import command.

    Data owns parsing, dialect handling, validation, and persistence, and
    authors the resulting storage manifest. The gateway forwards the caller
    payload unchanged: it never reads the source file and never selects a
    dialect on the caller's behalf.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.dataset_import_request.v1"] = (
        "api.dataset_import_request.v1"
    )
    payload: Mapping[str, object]


__all__ = (
    "DatasetImportRequest",
    "DatasetPrepareRequest",
)
