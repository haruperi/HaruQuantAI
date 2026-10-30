"""Neural Network application plugin service and task constraints.

Description:
    Implements the Neural Network application plugin service, delivering plugin
    registration metadata, navigation descriptor, and task trainer donor metadata.
    Enforces the confirmed no-op execution constraint for TaskNeuralNetworkTrainer
    per donor source audit (SRC-20261030-NEURAL-NOOP).

Purpose:
    FEAT-NEURAL-NETWORK: Backend plugin descriptor and task constraints for
    the Neural Network workspace.

Key Capabilities:
    - FR-neural-app-plugin-registration: Export NeuralNetwork application metadata.
    - FR-neural-task-trainer-descriptor: Provide donor trainer task metadata.
    - FR-neural-task-noop-constraint: Fail-closed interceptor for no-op donor task.

Python API Usage:
    from app.workspace.neural_network.app_neural_network import AppNeuralNetworkService

    service = AppNeuralNetworkService()
    plugin = service.get_plugin_descriptor()
    task = service.get_trainer_task_descriptor()
    result = service.execute_trainer_task(project_name="Demo")

CLI Usage:
    uv run python -c "from app.workspace.neural_network import (
        AppNeuralNetworkService,
    )"
"""

from __future__ import annotations

from typing import Final

from app.core.host.logging import get_logger
from app.core.lib.errors import JSONValue
from app.core.lib.responses import StandardResponse
from app.workspace.neural_network.app_neural_network_models import (
    NeuralNetworkPluginDescriptor,
    NeuralNetworkTrainerTaskDescriptor,
    NeuralTaskExecutionResult,
)
from app.workspace.neural_network.navigation import NeuralNavigation

logger: Final = get_logger(__name__)


class AppNeuralNetworkService:
    """Service providing Neural Network plugin registration and task metadata."""

    def __init__(self) -> None:
        """Initialize AppNeuralNetworkService with descriptors."""
        self._plugin_descriptor = NeuralNetworkPluginDescriptor()
        self._task_descriptor = NeuralNetworkTrainerTaskDescriptor()
        self._navigation = NeuralNavigation()
        logger.info(
            "Initialized AppNeuralNetworkService app_code=%s "
            "[FR-neural-app-plugin-registration]",
            self._plugin_descriptor.app_code,
        )

    def get_plugin_descriptor(self) -> NeuralNetworkPluginDescriptor:
        """Retrieve the plugin registration metadata descriptor.

        Returns:
            NeuralNetworkPluginDescriptor with name, app_code, and context path.
        """
        logger.info(
            "Retrieved plugin descriptor for %s [FR-neural-app-plugin-registration]",
            self._plugin_descriptor.app_code,
        )
        return self._plugin_descriptor

    def get_trainer_task_descriptor(self) -> NeuralNetworkTrainerTaskDescriptor:
        """Retrieve metadata descriptor for TaskNeuralNetworkTrainer.

        Returns:
            NeuralNetworkTrainerTaskDescriptor with donor settings and status.
        """
        logger.info(
            "Retrieved trainer task descriptor for %s "
            "[FR-neural-task-trainer-descriptor]",
            self._task_descriptor.type,
        )
        return self._task_descriptor

    def get_navigation(
        self, *, request_id: str
    ) -> StandardResponse[dict[str, JSONValue]]:
        """Retrieve standard navigation response.

        Args:
            request_id: Non-empty request identifier.

        Returns:
            StandardResponse containing navigation descriptor.
        """
        return self._navigation.get(request_id=request_id)

    def execute_trainer_task(
        self, *, project_name: str = ""
    ) -> NeuralTaskExecutionResult:
        """Attempt to dispatch the donor NeuralNetworkTrainer task.

        Enforces the confirmed NO-OP constraint from SRC-20261030-NEURAL-NOOP:
        the donor NeuralNetworkTrainerTask has an empty start() method and
        does not implement a real training algorithm.

        Args:
            project_name: Optional project identifier.

        Returns:
            NeuralTaskExecutionResult detailing the non-runnable no-op state.
        """
        logger.info(
            "Intercepted TaskNeuralNetworkTrainer execution for project=%s: "
            "donor start() is an empty NO-OP [FR-neural-task-noop-constraint]",
            project_name,
        )
        return NeuralTaskExecutionResult(
            task_type=self._task_descriptor.type,
            status="NO_OP",
            message=(
                "Donor TaskNeuralNetworkTrainer start() is a confirmed no-op; "
                "training is unavailable in HaruQuantAI per SRC-20261030-NEURAL-NOOP."
            ),
            is_no_op=True,
        )
