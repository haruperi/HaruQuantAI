"""Tests for NeuralNavigation metadata.

Description:
    Validates NeuralNavigation descriptor response, detached immutability,
    and non-silent requirement logging.

Purpose:
    FEAT-NEURAL-NETWORK: Verify navigation metadata conformity to WO-13-01.
"""

from __future__ import annotations

import pytest
from app.workspace.neural_network.navigation import NeuralNavigation


def test_hidden_navigation(caplog: pytest.LogCaptureFixture) -> None:
    """Verify NeuralNavigation returns exact hidden navigation descriptor."""
    with caplog.at_level("INFO"):
        nav = NeuralNavigation()
        resp = nav.get(request_id="n1")

    assert resp.to_dict() == {
        "request_id": "n1",
        "data": {
            "app_code": "NEURALNETWORK",
            "title": "Neural Network Trainer",
            "order": 50,
            "section": 0,
            "hidden": True,
        },
        "revision": None,
    }
    assert "FR-neural-navigation" in caplog.text


def test_navigation_detached() -> None:
    """Verify mutating returned descriptor does not mutate subsequent responses."""
    nav = NeuralNavigation()
    resp1 = nav.get(request_id="n1")
    data_dict = resp1.to_dict()["data"]
    assert isinstance(data_dict, dict)
    data_dict["hidden"] = False
    data_dict["order"] = 999
    data_dict["title"] = "Modified"

    resp2 = nav.get(request_id="n2")
    assert resp2.to_dict()["data"] == {
        "app_code": "NEURALNETWORK",
        "title": "Neural Network Trainer",
        "order": 50,
        "section": 0,
        "hidden": True,
    }
