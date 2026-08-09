"""Versioned trade-ownership contract."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator


class _TradeOwnership(BaseModel):
    """Private immutable ownership assignment."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.trade_ownership.v1"] = "trading.trade_ownership.v1"
    ownership_id: str
    owner_type: Literal["player", "supervised_automation", "automated"]
    owner_id: str
    account_id: str
    position_id: str
    trade_plan_id: str
    strategy_version: str
    session_id: str
    source_sequence: int
    released: bool = False

    @model_validator(mode="after")
    def _validate(self) -> Self:
        values = (
            self.ownership_id,
            self.owner_id,
            self.account_id,
            self.position_id,
            self.trade_plan_id,
            self.strategy_version,
            self.session_id,
        )
        if any(not value.strip() for value in values) or self.source_sequence < 0:
            raise ValueError("trade ownership identity is invalid")
        return self


__all__: list[str] = []
