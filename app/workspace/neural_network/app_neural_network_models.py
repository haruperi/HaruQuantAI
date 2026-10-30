"""Neural Network workspace data models.

Description:
    Defines Pydantic models for the Neural Network application plugin descriptor,
    navigation configuration, task trainer metadata, and execution constraints.

Purpose:
    FEAT-NEURAL-NETWORK: Provide strongly typed schemas for Neural Network plugin
    registration, observed donor metadata, and confirmed no-op task constraints.

Key Capabilities:
    - FR-neural-app-plugin-registration: Strongly typed plugin descriptor attributes.
    - FR-neural-task-trainer-descriptor: Donor TaskNeuralNetworkTrainer descriptor.
    - FR-neural-task-noop-constraint: Result model for no-op execution constraint.

Python API Usage:
    from app.workspace.neural_network.app_neural_network_models import (
        NeuralNetworkPluginDescriptor,
        NeuralNetworkTrainerTaskDescriptor,
    )

    plugin_desc = NeuralNetworkPluginDescriptor()
    task_desc = NeuralNetworkTrainerTaskDescriptor()

CLI Usage:
    uv run python -c "from app.workspace.neural_network import (
        NeuralNetworkPluginDescriptor,
    )"
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class NeuralNetworkPluginDescriptor(BaseModel):
    """Plugin registration descriptor for Neural Network Trainer."""

    name: str = Field(
        default="Neural Network Trainer", description="Plugin display name"
    )
    author: str = Field(default="Tomas Brynda", description="Plugin author")
    category: str = Field(default="App", description="Plugin category")
    product: str = Field(default="SQUANT", description="Target product")
    preferred_position: int = Field(
        default=10, description="Preferred menu position order"
    )
    context_path: str = Field(
        default="/NEURALNETWORK", description="Context root URL path"
    )
    app_code: str = Field(
        default="NEURALNETWORK", description="Application code identifier"
    )
    tooltip: str = Field(
        default="Neural Network Trainer", description="Hover tooltip description"
    )
    hidden: bool = Field(
        default=True, description="Whether hidden from primary navigation"
    )
    order: int = Field(default=50, description="Navigation display order")
    section: int = Field(default=0, description="Navigation menu section index")
    icon_class: str = Field(default="fa-home", description="Donor icon CSS class")
    url: str = Field(
        default="../NEURALNETWORK/index.html", description="Relative iframe/view URL"
    )
    iframe_id: str = Field(default="nnt-frame", description="Donor iframe element ID")
    link_id: str = Field(default="nnt-link", description="Donor navigation link ID")
    project: str | None = Field(
        default=None, description="Associated project identifier"
    )
    default_task_type: str | None = Field(
        default=None, description="Default task type if associated"
    )
    default_task_name: str | None = Field(
        default=None, description="Default task name if associated"
    )


class NeuralNetworkTrainerTaskDescriptor(BaseModel):
    """Task metadata descriptor for TaskNeuralNetworkTrainer."""

    type: str = Field(
        default="NeuralNetworkTrainer", description="Task type identifier"
    )
    name: str = Field(default="Neural Network Trainer", description="Display task name")
    author: str = Field(default="Tamas Takacs", description="Task author")
    category: str = Field(default="Task", description="Task category")
    product: str = Field(default="SQUANT", description="Product target")
    plugin_folder_name: str = Field(
        default="TaskNeuralNetworkTrainer", description="Donor plugin folder name"
    )
    preferred_position: int = Field(
        default=5, description="Task palette preferred position"
    )
    settings: list[str] = Field(
        default_factory=lambda: ["Data", "Options", "Rankings", "Notes"],
        description="Settings tabs in donor order",
    )
    running_status: int = Field(default=0, description="Running status integer code")
    is_runnable: bool = Field(
        default=False,
        description="Whether training computation is runnable (confirmed NO-OP)",
    )
    used_databanks: None = Field(default=None, description="Used databanks reference")
    output_databank: None = Field(default=None, description="Output databank reference")


class NeuralTaskExecutionResult(BaseModel):
    """Result of attempting to dispatch a neural network task."""

    task_type: str = Field(..., description="Task type dispatched")
    status: str = Field(..., description="Execution status code")
    message: str = Field(..., description="Informative status message")
    is_no_op: bool = Field(
        ..., description="Whether execution was intercepted as a confirmed no-op"
    )
