"""Custom function execution strategy block.

Description:
    Executes user-registered custom functions by string identifier with non-silent
    logging, raising NotImplementedError when unregistered to mirror StrategyQuant
    donor behavior.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-custom: Dynamic custom function invocation.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.custom_function import custom_function
    res = custom_function("my_custom_fn", 1, 2)
CLI Usage:
    uv run pytest tests/extend/blocks/test_functions.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.functions._common import (
    _CUSTOM_REGISTRY,
    register_custom_function,
)

logger = get_logger(__name__)

custom_function_spec = BlockSpec(
    id="function.custom_function",
    version="1.0.0",
    name="Custom Function",
    description="Executes a user-registered custom function by string identifier",
    category="functions",
    tags=("custom", "extension", "function"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(InputPort("function_name", PortType.STRING, "Unique function identifier"),),
    outputs=(OutputPort("value", PortType.ANY, "Custom function return value"),),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(custom_function_spec)
def custom_function(
    function_name: str,
    *args: Any,
    handler: Any = None,
    **kwargs: Any,
) -> Any:
    """Execute registered custom function by identifier.

    Args:
        function_name: Identifier of function.
        *args: Positional arguments.
        handler: Optional explicit callable override.
        **kwargs: Keyword arguments.

    Returns:
        Evaluation outcome.

    Raises:
        NotImplementedError: If function is unregistered and no handler is provided.
    """
    fn = handler if handler is not None else _CUSTOM_REGISTRY.get(function_name)
    if fn is None:
        logger.debug("FR-SERVICES-FUNCTION-CUSTOM: '%s' not registered", function_name)
        raise NotImplementedError(
            f"Custom function '{function_name}' is not registered."
        )

    res = fn(*args, **kwargs)
    logger.debug("FR-SERVICES-FUNCTION-CUSTOM: '%s' executed -> %s", function_name, res)
    return res


__all__ = [
    "custom_function",
    "custom_function_spec",
    "register_custom_function",
]
