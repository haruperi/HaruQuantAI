"""Shared response wrapping and utility helpers for Optimizer workspace.

Description:
    Provides canonical response wrapping and payload serialization helpers
    aligning with StandardResponse[T] instance envelope specifications.

Purpose:
    FEAT-OPTIMIZER-COMMON: Response envelope helpers and shared constants.

Key Capabilities:
    - FR-optimizer-wrap-response: Generic typed StandardResponse[T] construction.

Python API Usage:
    from app.workspace.optimizer.common import wrap_response
    resp = wrap_response(request_id="req_1", data=my_obj, json_payload=my_obj.to_dict())

CLI Usage:
    python -c "from app.workspace.optimizer.common import wrap_response; print(1)"
"""

from __future__ import annotations

from typing import Any, cast

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse

logger = get_logger(__name__)


def wrap_response[T](
    request_id: str,
    data: T,
    json_payload: Any,
    revision: int | None = None,
) -> StandardResponse[T]:
    """Validate json_payload through StandardResponse and attach typed data.

    Args:
        request_id: Operation request identifier.
        data: Typed domain entity payload.
        json_payload: JSON-serializable representation for validation.
        revision: Optional version counter.

    Returns:
        StandardResponse envelope enclosing typed data entity.
    """
    logger.debug("Wrapping response for request_id=%s", request_id)
    envelope: StandardResponse[Any] = StandardResponse(
        request_id=request_id,
        data=json_payload,
        revision=revision,
    )
    object.__setattr__(envelope, "data", data)
    return cast("StandardResponse[T]", envelope)
