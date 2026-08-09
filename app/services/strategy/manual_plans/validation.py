"""Manual-plan lineage isolation."""

# ruff: noqa: DOC201, DOC501

from collections.abc import Mapping

from app.services.strategy.intents.trade_plan import parse_trade_plan


def validate_manual_trade_plan(plan: Mapping[str, object]) -> dict[str, object]:
    """Validate player input through the same canonical TradePlan model."""
    material = dict(plan)
    author_ref = material.pop("author_ref", None)
    parsed = parse_trade_plan(material)
    if (
        parsed["author_type"] != "PLAYER"
        or not isinstance(author_ref, str)
        or not author_ref.strip()
    ):
        raise ValueError("manual plans require bounded player lineage")
    return parsed | {"author_ref": author_ref}


__all__ = ["validate_manual_trade_plan"]
