"""Strategy rule and AST block negaters catalog (15 definitions).

Description:
    Implements the 15 StrategyQuant negater snippets used to transform Long rules
    into symmetric Short rules (and vice versa) during symmetric strategy generation.
    Handles action direction inversion, boolean tree recursion, comparison reversal,
    oscillator midpoint reflection, band swapping, and Fibonacci/Pivot level inversion.

Purpose:
    FEAT-NEGATER-CATALOG: Deterministic AST opposite-direction transformation.

Key Capabilities:
    - FR-negater-actions: Invert market/stop entries and exits between Long and Short.
    - FR-negater-comparisons: Invert relational operators and directional trends.
    - FR-negater-oscillators: Mirror oscillator boundaries around midpoints (50 or 0).
    - FR-negater-registry: Central dispatcher for all 15 negater implementations.

Python API Usage:
    from app.extend.negater.catalog import BlockNegaterRegistry
    short_rule = BlockNegaterRegistry.negate_node("ActionsNegater", long_rule)

CLI Usage:
    python -c "from app.extend.negater.catalog import BlockNegaterRegistry; print(1)"
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from app.core.host.logging import get_logger

logger = get_logger(__name__)

_MIDPOINT_50: float = 100.0
_FIBO_MAX: float = 1.0


class ActionsNegater:
    """Inverts trading actions between Long and Short directions."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Invert action direction."""
        if isinstance(node, str):
            node = re.sub(
                r"\b(EnterAtMarket|EnterAtStop|EnterAtLimit)\(Long\)",
                r"__TEMP_\1_SHORT__",
                node,
            )
            node = re.sub(
                r"\b(EnterAtMarket|EnterAtStop|EnterAtLimit)\(Short\)",
                r"\1(Long)",
                node,
            )
            node = re.sub(
                r"__TEMP_(EnterAtMarket|EnterAtStop|EnterAtLimit)_SHORT__",
                r"\1(Short)",
                node,
            )
            node = re.sub(r"\bExitLong\b", "__TEMP_EXIT_SHORT__", node)
            node = re.sub(r"\bExitShort\b", "ExitLong", node)
            return re.sub(r"__TEMP_EXIT_SHORT__", "ExitShort", node)

        if isinstance(node, dict):
            res = dict(node)
            action_type = res.get("action_type") or res.get("type", "")
            direction = res.get("direction", "")

            if direction == "Long":
                res["direction"] = "Short"
            elif direction == "Short":
                res["direction"] = "Long"

            if action_type == "ExitLong":
                res["action_type"] = "ExitShort"
            elif action_type == "ExitShort":
                res["action_type"] = "ExitLong"
            return res

        return node


class AndOrNegater:
    """Preserves AND/OR boolean conjunction structure while recursing on children."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Recurse on boolean tree operands."""
        if isinstance(node, dict) and "children" in node:
            res = dict(node)
            res["children"] = [
                BlockNegaterRegistry.negate_node("ConditionsNegater", child)
                for child in node["children"]
            ]
            return res
        return node


class ComparisonsNegater:
    """Inverts comparison operators and directional trends."""

    OP_MAP: ClassVar[dict[str, str]] = {
        ">": "<",
        "<": ">",
        ">=": "<=",
        "<=": ">=",
        "==": "==",
        "IsGreater": "IsLower",
        "IsLower": "IsGreater",
        "CrossesAbove": "CrossesBelow",
        "CrossesBelow": "CrossesAbove",
        "IsRising": "IsFalling",
        "IsFalling": "IsRising",
    }

    @classmethod
    def negate(cls, node: Any) -> Any:
        """Invert comparison operator."""
        if isinstance(node, str):
            res_str = node
            for op, inv in [
                ("CrossesAbove", "CrossesBelow"),
                ("CrossesBelow", "CrossesAbove"),
                ("IsRising", "IsFalling"),
                ("IsFalling", "IsRising"),
                ("IsGreater", "IsLower"),
                ("IsLower", "IsGreater"),
                (">=", "<="),
                ("<=", ">="),
                (">", "<"),
                ("<", ">"),
            ]:
                if op in res_str:
                    return res_str.replace(op, inv)
            return res_str

        if isinstance(node, dict):
            dict_node: dict[str, Any] = dict(node)
            dict_op = dict_node.get("operator")
            if isinstance(dict_op, str) and dict_op in cls.OP_MAP:
                dict_node["operator"] = cls.OP_MAP[dict_op]
            return dict_node

        return node


class OscillatorComparisonsNegater:
    """Inverts comparisons and mirrors oscillator thresholds around midpoints."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Invert comparison and mirror oscillator threshold."""
        if isinstance(node, str):
            m = re.match(
                r"^(.*?)\s*(>|<|>=|<=|CrossesAbove|CrossesBelow)\s*([0-9.-]+)$",
                node.strip(),
            )
            if m:
                indicator, op, thresh_str = m.group(1), m.group(2), m.group(3)
                inv_op = ComparisonsNegater.OP_MAP.get(op, op)
                threshold = float(thresh_str)

                # Midpoint 50 for RSI/Stochastic/MFI
                if any(x in indicator for x in ("RSI", "Stochastic", "MFI")):
                    new_thresh = round(_MIDPOINT_50 - threshold, 4)
                else:
                    new_thresh = round(-threshold, 4)

                val_repr = int(new_thresh) if new_thresh.is_integer() else new_thresh
                return f"{indicator} {inv_op} {val_repr}"

        if isinstance(node, dict):
            dict_node: dict[str, Any] = dict(node)
            op = dict_node.get("operator", "")
            dict_node["operator"] = ComparisonsNegater.OP_MAP.get(op, op)
            threshold_val = dict_node.get("threshold")
            indicator = dict_node.get("indicator", "")
            if isinstance(threshold_val, (int, float)):
                if any(x in indicator for x in ("RSI", "Stochastic", "MFI")):
                    dict_node["threshold"] = _MIDPOINT_50 - threshold_val
                else:
                    dict_node["threshold"] = -threshold_val
            return dict_node

        return ComparisonsNegater.negate(node)


class CDataIndyNegater:
    """Swaps Open/Close or High/Low price extremes."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Swap High and Low."""
        if isinstance(node, str):
            node = re.sub(r"\bHigh\b", "__TEMP_HIGH__", node)
            node = re.sub(r"\bLow\b", "High", node)
            return re.sub(r"\b__TEMP_HIGH__\b", "Low", node)
        if isinstance(node, dict) and "field" in node:
            res = dict(node)
            if res["field"] == "High":
                res["field"] = "Low"
            elif res["field"] == "Low":
                res["field"] = "High"
            return res
        return node


class ConditionsNegater:
    """Composite conditions negater combining comparisons and directional flips."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Negate condition node."""
        if isinstance(node, str):
            if any(x in node for x in ("BollingerBands", "Bands", "Keltner")):
                return UpperLowerNegater.negate(node)
            if any(x in node for x in ("RSI", "Stochastic", "MFI", "CCI", "MACD")):
                return OscillatorComparisonsNegater.negate(node)
            return ComparisonsNegater.negate(node)
        return ComparisonsNegater.negate(node)


class UpperLowerNegater:
    """Swaps UpperBand and LowerBand in band indicators."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Swap Upper and Lower bands and invert comparison."""
        if isinstance(node, str):
            res_str = ComparisonsNegater.negate(node)
            res_str = re.sub(r"\bUpperBand\b", "__TEMP_UPPER__", res_str)
            res_str = re.sub(r"\bLowerBand\b", "UpperBand", res_str)
            res_str = re.sub(r"\b__TEMP_UPPER__\b", "LowerBand", res_str)
            res_str = re.sub(r"\.Upper\(", ".__TEMP_UPPER_CALL__(", res_str)
            res_str = re.sub(r"\.Lower\(", ".Upper(", res_str)
            return re.sub(r"\.__TEMP_UPPER_CALL__\(", ".Lower(", res_str)
        if isinstance(node, dict):
            dict_node: dict[str, Any] = dict(node)
            band = dict_node.get("band")
            if band == "Upper":
                dict_node["band"] = "Lower"
            elif band == "Lower":
                dict_node["band"] = "Upper"
            return ComparisonsNegater.negate(dict_node)
        return node


class FiboNegater:
    """Inverts Fibonacci retracement levels around 1.0."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Invert Fibonacci ratio."""
        if isinstance(node, dict) and "level" in node:
            res = dict(node)
            level = float(res["level"])
            res["level"] = round(_FIBO_MAX - level, 4)
            return res
        return node


class FractalNegater:
    """Swaps UpFractal and DownFractal."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Swap Fractal directions."""
        if isinstance(node, str):
            node = re.sub(r"\bUpFractal\b", "__TEMP_FRACTAL__", node)
            node = re.sub(r"\bDownFractal\b", "UpFractal", node)
            return re.sub(r"\b__TEMP_FRACTAL__\b", "DownFractal", node)
        return node


class PivotsNegater:
    """Swaps Support and Resistance pivot levels (R1 <-> S1, R2 <-> S2)."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Swap Resistance and Support pivots."""
        if isinstance(node, str):
            node = re.sub(r"\bR1\b", "__TEMP_R1__", node)
            node = re.sub(r"\bS1\b", "R1", node)
            node = re.sub(r"\b__TEMP_R1__\b", "S1", node)
            node = re.sub(r"\bR2\b", "__TEMP_R2__", node)
            node = re.sub(r"\bS2\b", "R2", node)
            return re.sub(r"\b__TEMP_R2__\b", "S2", node)
        return node


class UlcerNegater:
    """Negates Ulcer index conditions."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Invert comparison for ulcer index."""
        return ComparisonsNegater.negate(node)


class FormulaNegater:
    """Swaps arithmetic signs (+ <-> -)."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Swap addition and subtraction signs."""
        if isinstance(node, str):
            node = re.sub(r"\+", "__TEMP_PLUS__", node)
            node = re.sub(r"-", "+", node)
            return re.sub(r"__TEMP_PLUS__", "-", node)
        return node


class FunctionsNegater:
    """Swaps directional functions (Highest <-> Lowest)."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Swap Highest and Lowest."""
        if isinstance(node, str):
            node = re.sub(r"\bHighest\b", "__TEMP_HIGHEST__", node)
            node = re.sub(r"\bLowest\b", "Highest", node)
            return re.sub(r"\b__TEMP_HIGHEST__\b", "Lowest", node)
        return node


class CBlockNegater:
    """Negates custom block directional parameters."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Invert direction on custom block."""
        if isinstance(node, dict) and "direction" in node:
            res = dict(node)
            d = res["direction"]
            if isinstance(d, int):
                res["direction"] = -d
            else:
                res["direction"] = "Short" if d == "Long" else "Long"
            return res
        return node


class DefaultNegater:
    """Fallback negater applying comparison negation."""

    @staticmethod
    def negate(node: Any) -> Any:
        """Default fallback negation."""
        return ComparisonsNegater.negate(node)


class BlockNegaterRegistry:
    """Registry coordinating all 15 StrategyQuant negaters."""

    NEGATERS: ClassVar[dict[str, Any]] = {
        "ActionsNegater": ActionsNegater,
        "AndOrNegater": AndOrNegater,
        "ComparisonsNegater": ComparisonsNegater,
        "OscillatorComparisonsNegater": OscillatorComparisonsNegater,
        "CDataIndyNegater": CDataIndyNegater,
        "ConditionsNegater": ConditionsNegater,
        "UpperLowerNegater": UpperLowerNegater,
        "FiboNegater": FiboNegater,
        "FractalNegater": FractalNegater,
        "PivotsNegater": PivotsNegater,
        "UlcerNegater": UlcerNegater,
        "FormulaNegater": FormulaNegater,
        "FunctionsNegater": FunctionsNegater,
        "CBlockNegater": CBlockNegater,
        "DefaultNegater": DefaultNegater,
    }

    @classmethod
    def list_negaters(cls) -> tuple[str, ...]:
        """List all 15 registered negater identifiers."""
        return tuple(cls.NEGATERS.keys())

    @classmethod
    def negate_node(cls, negater_id: str, node: Any) -> Any:
        """Negate an AST node or rule using the designated negater.

        Args:
            negater_id: Name of the negater class.
            node: Node or rule representation (str, dict, or object).

        Returns:
            Negated node or rule.

        Raises:
            ValueError: If negater_id is unrecognized.
        """
        negater = cls.NEGATERS.get(negater_id)
        if negater is None:
            raise ValueError(f"Unknown negater: {negater_id}")
        logger.debug("Applying negater '%s' to node", negater_id)
        return negater.negate(node)
