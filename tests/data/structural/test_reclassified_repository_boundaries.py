"""Structural-tier verification for repository-scale Data scans."""

from tests.data.unit.test_broker_contract import (
    structural_the_allow_list_covers_every_adapter_call_data_makes,
)
from tests.data.unit.test_workflow_usage_parity import (
    structural_data_workflow_registry_has_one_complete_program_per_active_workflow,
)


def test_broker_allow_list_covers_every_data_call() -> None:
    """Run the repository-scale broker adapter call scan."""
    structural_the_allow_list_covers_every_adapter_call_data_makes()


def test_workflow_registry_has_one_program_per_active_workflow() -> None:
    """Run the repository-scale workflow usage reconciliation."""
    structural_data_workflow_registry_has_one_complete_program_per_active_workflow()
