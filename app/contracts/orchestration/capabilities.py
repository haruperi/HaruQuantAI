"""Orchestration domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.orchestration.ports import (
        DefineProjectsCapability,
        EvaluateConditionsCapability,
        RunDomainTasksCapability,
        RunTasksCapability,
        RunUtilityTasksCapability,
        TrackRunHistoryCapability,
        TrainNetworksCapability,
    )

DEFINE_PROJECTS_CAPABILITY: CapabilityKey[DefineProjectsCapability] = CapabilityKey(
    name="orchestration.define-projects",
    major=1,
)

RUN_TASKS_CAPABILITY: CapabilityKey[RunTasksCapability] = CapabilityKey(
    name="orchestration.run-tasks",
    major=1,
)

EVALUATE_CONDITIONS_CAPABILITY: CapabilityKey[EvaluateConditionsCapability] = (
    CapabilityKey(
        name="orchestration.evaluate-conditions",
        major=1,
    )
)

RUN_DOMAIN_TASKS_CAPABILITY: CapabilityKey[RunDomainTasksCapability] = CapabilityKey(
    name="orchestration.run-domain-tasks",
    major=1,
)

RUN_UTILITY_TASKS_CAPABILITY: CapabilityKey[RunUtilityTasksCapability] = CapabilityKey(
    name="orchestration.run-utility-tasks",
    major=1,
)

TRACK_RUN_HISTORY_CAPABILITY: CapabilityKey[TrackRunHistoryCapability] = CapabilityKey(
    name="orchestration.track-run-history",
    major=1,
)

TRAIN_NETWORKS_CAPABILITY: CapabilityKey[TrainNetworksCapability] = CapabilityKey(
    name="orchestration.train-networks",
    major=1,
)
