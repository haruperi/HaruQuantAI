"""Unit tests for Neural Network application plugin service, models, and task constraints.

Description:
    Tests AppNeuralNetworkService, plugin descriptors, donor task metadata,
    no-op execution constraint (SRC-20261030-NEURAL-NOOP), and non-silent
    requirement logging.

Purpose:
    FEAT-NEURAL-NETWORK: Verify service parity and task constraints for Neural Network.
"""

from __future__ import annotations

import pytest
from app.workspace.neural_network.app_neural_network import AppNeuralNetworkService
from app.workspace.neural_network.app_neural_network_models import (
    NeuralNetworkPluginDescriptor,
    NeuralNetworkTrainerTaskDescriptor,
)


def test_neural_network_plugin_descriptor(caplog: pytest.LogCaptureFixture) -> None:
    """Verify plugin descriptor metadata matches donor specification."""
    with caplog.at_level("INFO"):
        service = AppNeuralNetworkService()
        descriptor = service.get_plugin_descriptor()

    assert descriptor.name == "Neural Network Trainer"
    assert descriptor.author == "Tomas Brynda"
    assert descriptor.category == "App"
    assert descriptor.product == "SQUANT"
    assert descriptor.preferred_position == 10
    assert descriptor.context_path == "/NEURALNETWORK"
    assert descriptor.app_code == "NEURALNETWORK"
    assert descriptor.tooltip == "Neural Network Trainer"
    assert descriptor.hidden is True
    assert descriptor.order == 50
    assert descriptor.section == 0
    assert descriptor.icon_class == "fa-home"
    assert descriptor.url == "../NEURALNETWORK/index.html"
    assert descriptor.iframe_id == "nnt-frame"
    assert descriptor.link_id == "nnt-link"
    assert descriptor.project is None
    assert descriptor.default_task_type is None
    assert descriptor.default_task_name is None
    assert "FR-neural-app-plugin-registration" in caplog.text


def test_neural_network_task_descriptor(caplog: pytest.LogCaptureFixture) -> None:
    """Verify TaskNeuralNetworkTrainer descriptor matches donor specification."""
    service = AppNeuralNetworkService()
    with caplog.at_level("INFO"):
        task = service.get_trainer_task_descriptor()

    assert task.type == "NeuralNetworkTrainer"
    assert task.name == "Neural Network Trainer"
    assert task.author == "Tamas Takacs"
    assert task.category == "Task"
    assert task.product == "SQUANT"
    assert task.plugin_folder_name == "TaskNeuralNetworkTrainer"
    assert task.preferred_position == 5
    assert task.settings == ["Data", "Options", "Rankings", "Notes"]
    assert task.running_status == 0
    assert task.is_runnable is False
    assert task.used_databanks is None
    assert task.output_databank is None
    assert "FR-neural-task-trainer-descriptor" in caplog.text


def test_neural_network_navigation_delegation() -> None:
    """Verify service delegates navigation to NeuralNavigation."""
    service = AppNeuralNetworkService()
    resp = service.get_navigation(request_id="serv-1")
    assert resp.to_dict() == {
        "request_id": "serv-1",
        "data": {
            "app_code": "NEURALNETWORK",
            "title": "Neural Network Trainer",
            "order": 50,
            "section": 0,
            "hidden": True,
        },
        "revision": None,
    }


def test_neural_network_task_execution_blocked(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify TaskNeuralNetworkTrainer start is blocked and reports confirmed NO-OP."""
    service = AppNeuralNetworkService()
    with caplog.at_level("INFO"):
        result = service.execute_trainer_task(project_name="TestProject")

    assert result.task_type == "NeuralNetworkTrainer"
    assert result.status == "NO_OP"
    assert result.is_no_op is True
    assert "confirmed no-op" in result.message
    assert "SRC-20261030-NEURAL-NOOP" in result.message
    assert "FR-neural-task-noop-constraint" in caplog.text


def test_custom_models() -> None:
    """Verify descriptor model immutability and custom overrides."""
    custom_plugin = NeuralNetworkPluginDescriptor(
        project="AlphaProject",
        default_task_type="NeuralNetworkTrainer",
        default_task_name="CustomTrainer",
    )
    assert custom_plugin.project == "AlphaProject"
    assert custom_plugin.default_task_type == "NeuralNetworkTrainer"
    assert custom_plugin.default_task_name == "CustomTrainer"

    custom_task = NeuralNetworkTrainerTaskDescriptor(
        preferred_position=7,
        settings=["Data", "Rankings"],
    )
    assert custom_task.preferred_position == 7
    assert custom_task.settings == ["Data", "Rankings"]
