"""Function-only factories and opaque handle operations for Portfolio."""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel

from app.services.portfolio._settings import PortfolioSettings, RebalanceSchedule
from app.services.portfolio.allocation.service import AllocationService
from app.services.portfolio.api.service import PortfolioService
from app.services.portfolio.construction.service import ConstructionService
from app.services.portfolio.contracts.allocations import (
    ActivePortfolioAllocation,
    DriftObservation,
    PortfolioRebalanceAction,
    PortfolioRebalancePlan,
)
from app.services.portfolio.contracts.definitions import PortfolioDefinition
from app.services.portfolio.contracts.errors import (
    PORTFOLIO_ERROR_CATALOG,
    PortfolioError,
)
from app.services.portfolio.contracts.requests import (
    EvidenceReferenceSet,
    FixedWeightInput,
    PortfolioConstructionRequest,
    StrategyAllocationRef,
)
from app.services.portfolio.contracts.results import (
    PortfolioComponentWeight,
    PortfolioConstructionResult,
)
from app.services.portfolio.evidence.validator import ValidatedConstructionEvidence
from app.services.portfolio.orchestration.workflows import (
    ConstructionEvidenceInputs,
    PortfolioReviewResult,
    PortfolioWorkflowDependencies,
    PortfolioWorkflowService,
)
from app.services.portfolio.rebalancing.cross_account import (
    CommonModeExposureReport,
    CrossAccountCorrelationReport,
)
from app.services.portfolio.rebalancing.service import RebalancingService
from app.services.portfolio.state.repository import PortfolioRepository
from app.utils import to_json_safe

_VALUE_TYPES = MappingProxyType(
    {
        value_type.__name__: value_type
        for value_type in (
            ActivePortfolioAllocation,
            CommonModeExposureReport,
            ConstructionEvidenceInputs,
            CrossAccountCorrelationReport,
            DriftObservation,
            EvidenceReferenceSet,
            FixedWeightInput,
            PortfolioComponentWeight,
            PortfolioConstructionRequest,
            PortfolioConstructionResult,
            PortfolioDefinition,
            PortfolioRebalanceAction,
            PortfolioRebalancePlan,
            PortfolioReviewResult,
            PortfolioSettings,
            RebalanceSchedule,
            StrategyAllocationRef,
            ValidatedConstructionEvidence,
        )
    }
)

_HANDLE_TYPES = (
    AllocationService,
    ConstructionService,
    PortfolioRepository,
    PortfolioService,
    PortfolioWorkflowDependencies,
    PortfolioWorkflowService,
    RebalancingService,
)

_HANDLE_OPERATIONS = MappingProxyType(
    {
        AllocationService: frozenset({"activate"}),
        ConstructionService: frozenset({"construct"}),
        PortfolioRepository: frozenset(
            {
                "active",
                "activate",
                "allocation",
                "definition",
                "history",
                "plan",
                "save_construction",
                "save_definition",
                "save_plan",
            }
        ),
        PortfolioService: frozenset(
            {
                "activate",
                "assess_drift",
                "construct",
                "definition",
                "history",
                "register_definition",
                "recompute_measurement",
                "rollback",
                "status",
                "submit_rebalance",
            }
        ),
        PortfolioWorkflowService: frozenset(
            {
                "activate",
                "assess_drift",
                "construct",
                "coordinate_review",
                "recompute_measurement",
                "rollback",
                "submit_rebalance",
                "validate_construction",
            }
        ),
        RebalancingService: frozenset(
            {
                "assess",
                "assess_common_mode_exposure",
                "measure_cross_account_correlation",
            }
        ),
    }
)


def create_portfolio_value(value_type: str, /, **fields_: object) -> object:
    """Construct one documented Portfolio value without exposing its class.

    Args:
        value_type: Exact registered internal value type name.
        **fields_: Constructor fields for the selected value.

    Returns:
        Opaque validated Portfolio value.

    Raises:
        ValueError: If the requested value type is not registered.
    """
    constructor: Any = _VALUE_TYPES.get(value_type)
    if constructor is None:
        message = f"Unknown Portfolio value type: {value_type}"
        raise ValueError(message)
    return constructor(**fields_)


def dump_portfolio_value(value: object) -> dict[str, object]:
    """Serialize one Portfolio value into bounded JSON-safe fields.

    Args:
        value: Opaque Portfolio value.

    Returns:
        Detached JSON-safe field mapping.

    Raises:
        ValueError: If the value is not a registered Portfolio value.
    """
    if not is_portfolio_value(value):
        raise ValueError("value must be a registered Portfolio value")
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", warnings=False)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_json_safe(getattr(value, field.name))
            for field in fields(value)
        }
    raise ValueError("Portfolio value does not support serialization")


def get_portfolio_value_field(value: object, field: str) -> object:
    """Read one public field from an opaque Portfolio value.

    Args:
        value: Opaque registered Portfolio value.
        field: Public field name.

    Returns:
        Field value.

    Raises:
        ValueError: If the value or field is invalid.
    """
    if not is_portfolio_value(value):
        raise ValueError("value must be a registered Portfolio value")
    if not field or field.startswith("_") or not hasattr(value, field):
        message = f"Unknown Portfolio value field: {field}"
        raise ValueError(message)
    return getattr(value, field)


def is_portfolio_value(value: object, value_type: str | None = None) -> bool:
    """Return whether an object is a registered Portfolio value.

    Args:
        value: Candidate object.
        value_type: Optional exact registered type name.

    Returns:
        Whether the object matches the requested Portfolio value type.
    """
    if value_type is not None:
        expected = _VALUE_TYPES.get(value_type)
        return expected is not None and isinstance(value, expected)
    return isinstance(value, tuple(_VALUE_TYPES.values()))


def create_portfolio_handle(
    handle_type: str,
    /,
    *args: object,
    **kwargs: object,
) -> object:
    """Construct one opaque Portfolio service or repository handle.

    Args:
        handle_type: Registered handle type name.
        *args: Positional constructor dependencies.
        **kwargs: Keyword constructor dependencies.

    Returns:
        Opaque Portfolio handle.

    Raises:
        ValueError: If the handle type is unknown.
    """
    constructors: dict[str, Any] = {handle.__name__: handle for handle in _HANDLE_TYPES}
    constructor: Any = constructors.get(handle_type)
    if constructor is None:
        message = f"Unknown Portfolio handle type: {handle_type}"
        raise ValueError(message)
    return constructor(*args, **kwargs)


def is_portfolio_handle(handle: object, handle_type: str | None = None) -> bool:
    """Return whether an object is a registered Portfolio handle.

    Args:
        handle: Candidate object.
        handle_type: Optional exact registered handle type name.

    Returns:
        Whether the object matches the requested handle type.
    """
    if handle_type is not None:
        expected = next(
            (item for item in _HANDLE_TYPES if item.__name__ == handle_type),
            None,
        )
        return expected is not None and isinstance(handle, expected)
    return isinstance(handle, _HANDLE_TYPES)


def execute_portfolio_handle_operation(
    handle: object,
    operation: str,
    /,
    *args: object,
    **kwargs: object,
) -> object:
    """Execute one allow-listed operation on an opaque Portfolio handle.

    Args:
        handle: Opaque Portfolio handle.
        operation: Allow-listed operation name.
        *args: Positional operation inputs.
        **kwargs: Keyword operation inputs.

    Returns:
        Direct operation result or coroutine for asynchronous operations.

    Raises:
        ValueError: If the handle or operation is unsupported.
    """
    handle_class = next(
        (item for item in _HANDLE_TYPES if isinstance(handle, item)),
        None,
    )
    if handle_class is None:
        raise ValueError("handle must be a registered Portfolio handle")
    allowed = _HANDLE_OPERATIONS.get(handle_class, frozenset())
    if operation not in allowed:
        message = f"Unsupported Portfolio handle operation: {operation}"
        raise ValueError(message)
    method = getattr(handle, operation)
    result = method(*args, **kwargs)
    if inspect.isawaitable(result):
        return result
    return result


def get_portfolio_error_catalog() -> Mapping[str, object]:
    """Return the immutable Portfolio error catalogue.

    Returns:
        Immutable code-to-definition mapping.
    """
    return PORTFOLIO_ERROR_CATALOG


def to_portfolio_error_payload(
    code: str,
    detail: str = "UNSPECIFIED",
) -> object:
    """Build one structured Portfolio error response.

    Args:
        code: Registered Portfolio error code.
        detail: Bounded non-sensitive detail.

    Returns:
        Utils standard response carrying Portfolio error evidence.
    """
    return PortfolioError(code, detail).to_payload()


__all__ = [
    "create_portfolio_handle",
    "create_portfolio_value",
    "dump_portfolio_value",
    "execute_portfolio_handle_operation",
    "get_portfolio_error_catalog",
    "get_portfolio_value_field",
    "is_portfolio_handle",
    "is_portfolio_value",
    "to_portfolio_error_payload",
]
