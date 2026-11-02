"""Actions negater conforming to StrategyQuant ActionsNegater snippet.

Description:
    Inverts trading actions between Long and Short directions, swapping market,
    stop, and limit entry orders, exit rules, and attached exit methods.

Purpose:
    FEAT-NEGATER-ACTIONS: StrategyQuant donor-faithful actions negation.

Key Capabilities:
    - FR-NEGATER-ACTIONS-INVERT: Invert action directions (Long <-> Short, 1 <-> -1).
    - FR-NEGATER-ACTIONS-EXIT: Invert exit actions and child exit methods.

Python API Usage:
    from app.extend.negater.actions_negater import ActionsNegater
    short_action = ActionsNegater.negate("EnterAtMarket(Long)")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)


def _negate_str(node: str) -> str:
    """Invert direction inside a pseudo-code action string."""
    res_str = re.sub(
        r"\b(EnterAtMarket|EnterAtStop|EnterAtLimit)\(Long\)",
        r"__TEMP_\1_SHORT__",
        node,
    )
    res_str = re.sub(
        r"\b(EnterAtMarket|EnterAtStop|EnterAtLimit)\(Short\)",
        r"\1(Long)",
        res_str,
    )
    res_str = re.sub(
        r"__TEMP_(EnterAtMarket|EnterAtStop|EnterAtLimit)_SHORT__",
        r"\1(Short)",
        res_str,
    )
    res_str = re.sub(r"\bExitLong\b", "__TEMP_EXIT_SHORT__", res_str)
    res_str = re.sub(r"\bExitShort\b", "ExitLong", res_str)
    return re.sub(r"__TEMP_EXIT_SHORT__", "ExitShort", res_str)


def _negate_dict(
    res: dict[str, Any],
    negate_fn: Any,
    strategy: Any,
) -> dict[str, Any]:
    """Invert direction inside an action dictionary."""
    direction = res.get("direction")
    if direction == "Long":
        res["direction"] = "Short"
    elif direction == "Short":
        res["direction"] = "Long"
    elif direction == 1:
        res["direction"] = -1
    elif direction == -1:
        res["direction"] = 1

    action_type = res.get("action_type") or res.get("type", "")
    if action_type == "ExitLong":
        res["action_type"] = "ExitShort"
    elif action_type == "ExitShort":
        res["action_type"] = "ExitLong"

    if "exit_methods" in res and isinstance(res["exit_methods"], list):
        res["exit_methods"] = [
            negate_fn(em, strategy=strategy) for em in res["exit_methods"]
        ]
    return res


def _negate_obj(node: Any) -> Any:
    """Invert direction on an order or action object."""
    if hasattr(node, "direction"):
        curr_dir = node.direction
        if curr_dir == "Long":
            node.direction = "Short"
        elif curr_dir == "Short":
            node.direction = "Long"
        elif isinstance(curr_dir, int):
            node.direction = -curr_dir
    return node


class ActionsNegater(Negater):
    """Inverts trading actions between Long and Short (SortOrder=10000)."""

    order: ClassVar[int] = 10_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Invert action direction across string, dict, or object representations.

        Args:
            node: Target action representation.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted action representation.
        """
        logger.debug("FR-NEGATER-ACTIONS-INVERT: negating action node")
        if isinstance(node, str):
            return _negate_str(node)
        if isinstance(node, dict):
            return _negate_dict(dict(node), cls.negate, strategy)
        return _negate_obj(node)
