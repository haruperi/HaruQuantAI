"""Neural Network navigation provider.

Description:
    Provides observed navigation metadata for the Neural Network workspace.
    Modeled after donor AppNeuralNetwork module registration.

Purpose:
    FEAT-NEURAL-NETWORK: Expose observed hidden navigation metadata descriptor.

Key Capabilities:
    - FR-neural-navigation: Return detached descriptor with app_code 'NEURALNETWORK',
      title 'Neural Network Trainer', order 50, section 0, and hidden True.

Python API Usage:
    from app.workspace.neural_network.navigation import NeuralNavigation

    nav = NeuralNavigation()
    response = nav.get(request_id="n1")

CLI Usage:
    uv run python -c "from app.workspace.neural_network.navigation import (
        NeuralNavigation,
    )"
"""

from __future__ import annotations

from typing import Final

from app.core.host.logging import get_logger
from app.core.lib.errors import JSONValue
from app.core.lib.responses import StandardResponse

logger: Final = get_logger(__name__)


class NeuralNavigation:
    """Provider for Neural Network workspace navigation metadata."""

    def __init__(self) -> None:
        """Initialize NeuralNavigation with no arguments."""
        logger.info(
            "Initialized NeuralNavigation [FR-neural-navigation]",
        )

    def get(self, *, request_id: str) -> StandardResponse[dict[str, JSONValue]]:
        """Return Neural Network navigation metadata.

        Args:
            request_id: Non-empty request identifier.

        Returns:
            StandardResponse containing detached dictionary of navigation metadata.
        """
        payload: dict[str, JSONValue] = {
            "app_code": "NEURALNETWORK",
            "title": "Neural Network Trainer",
            "order": 50,
            "section": 0,
            "hidden": True,
        }
        logger.info(
            "Retrieved NeuralNetwork navigation metadata for request_id=%s "
            "[FR-neural-navigation]",
            request_id,
        )
        return StandardResponse(
            request_id=request_id,
            data=payload,
            revision=None,
        )
