"""Public Simulation error-payload conversion."""

from app.services.simulator.errors.exception import SimulationError
from app.utils import logger


def to_simulation_error_payload(error: Exception) -> dict[str, object]:
    """Convert an exception into a bounded redacted public payload.

    Args:
        error: Exception to classify.

    Returns:
        Bounded payload containing only controlled fields.
    """
    logger.info("Converting an exception to a Simulation error payload")
    controlled = (
        error
        if isinstance(error, SimulationError)
        else SimulationError(
            "SIM_INTERNAL_ERROR",
            "Simulation failed safely",
        )
    )
    payload: dict[str, object] = {
        "code": controlled.code,
        "message": controlled.message,
    }
    if controlled.details:
        payload["details"] = dict(controlled.details)
    if controlled.request_id is not None:
        payload["request_id"] = controlled.request_id
    if controlled.correlation_id is not None:
        payload["correlation_id"] = controlled.correlation_id
    return payload


__all__ = ["to_simulation_error_payload"]
