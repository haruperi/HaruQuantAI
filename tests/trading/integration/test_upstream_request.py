"""Workflow integration for the governed upstream request boundary."""

# ruff: noqa: INP001

import pytest
from app.services.trading.contracts import TradingRequest
from pydantic import ValidationError
from tests.trading.conftest import trading_request


def test_raw_signal_translation_is_rejected() -> None:
    """Raw signal dictionaries cannot enter the immutable Trading request contract."""
    material = trading_request().model_dump(mode="python")
    material["raw_signal"] = {"direction": "BUY"}
    with pytest.raises(ValidationError):
        TradingRequest.model_validate(material)
