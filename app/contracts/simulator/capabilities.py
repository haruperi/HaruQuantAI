"""Simulator domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.simulator.ports import (
        CacheEvaluationsCapability,
        CalculateCostsCapability,
        CalculateProfilesCapability,
        CommitResultsCapability,
        ConfigureEngineCapability,
        DistributeEvaluationsCapability,
        ManageExitsCapability,
        ModelPrecisionCapability,
        PerturbInputsCapability,
        RunIndicatorsCapability,
        SimulateOrdersCapability,
        SimulateStockpickersCapability,
    )

CONFIGURE_ENGINE_CAPABILITY: CapabilityKey[ConfigureEngineCapability] = CapabilityKey(
    name="simulator.configure-engine",
    major=1,
)

MODEL_PRECISION_CAPABILITY: CapabilityKey[ModelPrecisionCapability] = CapabilityKey(
    name="simulator.model-precision",
    major=1,
)

SIMULATE_ORDERS_CAPABILITY: CapabilityKey[SimulateOrdersCapability] = CapabilityKey(
    name="simulator.simulate-orders",
    major=1,
)

CALCULATE_COSTS_CAPABILITY: CapabilityKey[CalculateCostsCapability] = CapabilityKey(
    name="simulator.calculate-costs",
    major=1,
)

MANAGE_EXITS_CAPABILITY: CapabilityKey[ManageExitsCapability] = CapabilityKey(
    name="simulator.manage-exits",
    major=1,
)

RUN_INDICATORS_CAPABILITY: CapabilityKey[RunIndicatorsCapability] = CapabilityKey(
    name="simulator.run-indicators",
    major=1,
)

COMMIT_RESULTS_CAPABILITY: CapabilityKey[CommitResultsCapability] = CapabilityKey(
    name="simulator.commit-results",
    major=1,
)

CACHE_EVALUATIONS_CAPABILITY: CapabilityKey[CacheEvaluationsCapability] = CapabilityKey(
    name="simulator.cache-evaluations",
    major=1,
)

CALCULATE_PROFILES_CAPABILITY: CapabilityKey[CalculateProfilesCapability] = (
    CapabilityKey(
        name="simulator.calculate-profiles",
        major=1,
    )
)

PERTURB_INPUTS_CAPABILITY: CapabilityKey[PerturbInputsCapability] = CapabilityKey(
    name="simulator.perturb-inputs",
    major=1,
)

DISTRIBUTE_EVALUATIONS_CAPABILITY: CapabilityKey[DistributeEvaluationsCapability] = (
    CapabilityKey(
        name="simulator.distribute-evaluations",
        major=1,
    )
)

SIMULATE_STOCKPICKERS_CAPABILITY: CapabilityKey[SimulateStockpickersCapability] = (
    CapabilityKey(
        name="simulator.simulate-stockpickers",
        major=1,
    )
)
