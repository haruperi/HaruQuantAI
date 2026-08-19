"""API response projection for the Markets feature."""

from __future__ import annotations

from collections.abc import Callable

from app.services.api import build_api_metadata, build_api_response


def build_gateway_response(
    response: object,
    *,
    request_id: str,
    route: str,
    operation: str,
    success_message: str,
    failure_message: str,
    source_id: str | None = None,
    include_technicals: bool = False,
    technical_builder: Callable[..., dict[str, float | None]],
) -> object:
    """Normalize one Data response into the API envelope.

    Args:
        response: Data standard response.
        request_id: Canonical request identifier.
        route: Canonical route path.
        operation: Canonical operation identifier.
        success_message: Successful response message.
        failure_message: Failed response message.
        source_id: Resolved provider for optional technical evidence.
        include_technicals: Whether to orchestrate Indicators enrichment.
        technical_builder: Injected technical-evidence orchestration function.

    Returns:
        Validated API response envelope.
    """
    response_status = str(getattr(response, "status", "success"))
    data_payload = getattr(response, "data", None)
    if response_status == "success" and data_payload and include_technicals:
        dumped = data_payload.model_dump(mode="json")
        dumped["rows"] = [
            {
                **row,
                **technical_builder(
                    str(source_id),
                    str(row["symbol"]),
                    last_price=(
                        float(row["last"]) if row.get("last") is not None else None
                    ),
                    request_id=request_id,
                ),
            }
            for row in dumped["rows"]
        ]
        data_payload = dumped

    upstream_error = getattr(response, "error", None)
    gateway_error = None
    if response_status != "success" and upstream_error is not None:
        gateway_error = {
            "code": "UPSTREAM_UNAVAILABLE",
            "message": str(getattr(upstream_error, "message", failure_message)),
            "details": {
                "upstream_code": str(getattr(upstream_error, "code", "UNKNOWN_ERROR"))
            },
            "retryable": bool(getattr(upstream_error, "retryable", False)),
            "request_id": request_id,
            "trace_id": None,
        }
    return build_api_response(
        status=response_status,
        message=success_message if response_status == "success" else failure_message,
        data=data_payload,
        error=gateway_error,
        metadata=build_api_metadata(
            request_id=request_id,
            route=route,
            operation=operation,
            side_effect="read",
        ),
    )


__all__ = ("build_gateway_response",)
