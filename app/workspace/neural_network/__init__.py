"""Neural Network workspace package.

Description:
    Provides neural network navigation, application plugin descriptors,
    and task specification constraints.

Purpose:
    FEAT-NEURAL-NETWORK: Neural network workspace capabilities and models.

Key Capabilities:
    - FR-neural-navigation: Observed hidden navigation descriptor.
    - FR-neural-app-plugin-registration: AppNeuralNetwork plugin descriptor.
    - FR-neural-task-trainer-descriptor: TaskNeuralNetworkTrainer donor metadata.
    - FR-neural-task-noop-constraint: Non-runnable constraint for no-op donor task.

Python API Usage:
    from app.workspace.neural_network import (
        AppNeuralNetworkService,
        NeuralNavigation,
        NeuralNetworkPluginDescriptor,
        NeuralNetworkTrainerTaskDescriptor,
    )

CLI Usage:
    uv run python -c "from app.workspace.neural_network import AppNeuralNetworkService"
"""

from __future__ import annotations

from app.workspace.neural_network.app_neural_network import AppNeuralNetworkService
from app.workspace.neural_network.app_neural_network_models import (
    NeuralNetworkPluginDescriptor,
    NeuralNetworkTrainerTaskDescriptor,
    NeuralTaskExecutionResult,
)
from app.workspace.neural_network.navigation import NeuralNavigation

__all__ = [
    "AppNeuralNetworkService",
    "NeuralNavigation",
    "NeuralNetworkPluginDescriptor",
    "NeuralNetworkTrainerTaskDescriptor",
    "NeuralTaskExecutionResult",
]
