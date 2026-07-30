"""Shared genuine-evidence infrastructure for Optimization workflows."""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.services.data import build_market_dataset
from tests.optimization.usage._support import (
    genuine_execution_bundle,
    search_request,
)
from tests.simulator.usage.workflows._support import live_market_dataset

_DATASET_ENV = "HARU_WORKFLOW_MARKET_DATASET"


def live_search_request(dataset: object) -> object:
    """Bind one bounded search request to genuine Data provenance."""
    return search_request(dataset)


def captured_market_dataset() -> object:
    """Load runner-captured market evidence or retrieve genuine MT5 data."""
    captured = os.environ.get(_DATASET_ENV)
    if captured:
        return build_market_dataset(
            **json.loads(Path(captured).read_text(encoding="utf-8"))
        )
    return live_market_dataset()


__all__ = [
    "_DATASET_ENV",
    "captured_market_dataset",
    "genuine_execution_bundle",
    "live_market_dataset",
    "live_search_request",
]
