"""Trading runtime configuration contracts.

The models in this module are immutable, JSON-safe, and secret-reference only.
They perform no environment reads, file reads, broker calls, or secret
resolution at import time.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.trading.contracts import (
    MutationCapability,
    SideEffectMode,
    TradingRoute,
)
from app.utils.logger import logger

CURRENCY_CODE_LENGTH = 3


class TradingConfigModel(BaseModel):
    """Base class for immutable trading configuration models."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SecretReference(TradingConfigModel):
    """Opaque reference to a secret managed outside trading config.

    Attributes:
        reference: Secret reference URI or key.
        version: Optional secret version selector.
        required: Whether this reference must resolve before runtime use.
    """

    reference: str
    version: str | None = None
    required: bool = True

    @model_validator(mode="after")
    def validate_reference(self) -> SecretReference:
        """Validate the secret reference has no raw secret shape.

        Returns:
            SecretReference: Validated secret reference.

        Raises:
            ValueError: If the reference is blank or appears to contain a raw
                secret assignment.
        """
        logger.info("Validating trading secret reference.")
        if not self.reference.strip():
            raise ValueError("secret reference must be non-empty.")
        lowered = self.reference.lower()
        if "=" in self.reference or any(
            token in lowered for token in ("password:", "token:", "secret:")
        ):
            raise ValueError("secret references must not contain raw secret values.")
        return self

    def redacted(self) -> str:
        """Return a redacted display value for this reference.

        Returns:
            str: Redacted reference marker.
        """
        logger.debug("Redacting secret reference {}.", self.reference)
        return f"{self.reference}#[REDACTED]"


class RouteSettings(TradingConfigModel):
    """Route enablement and mutation capability configuration."""

    enabled_routes: frozenset[TradingRoute] = Field(
        default_factory=lambda: frozenset(
            {TradingRoute.SIM, TradingRoute.PAPER, TradingRoute.SHADOW}
        )
    )
    allow_live_mutations: bool = False
    default_mutation_capability: MutationCapability = MutationCapability.PACKAGED_ONLY
    promotion_stage_assignments: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_routes(self) -> RouteSettings:
        """Validate route settings.

        Returns:
            RouteSettings: Validated route settings.
        """
        logger.info("Validating trading route settings.")
        if self.allow_live_mutations and TradingRoute.LIVE not in self.enabled_routes:
            raise ValueError("live route must be enabled before live mutations.")
        return self

    def passing_gate_side_effect(self) -> SideEffectMode:
        """Return the side-effect mode for a passing live gate.

        Returns:
            SideEffectMode: Packaged-only when live mutations are disabled.
        """
        logger.info(
            "Resolved passing gate side effect with live mutations enabled={}.",
            self.allow_live_mutations,
        )
        if not self.allow_live_mutations:
            return SideEffectMode.PACKAGED_ONLY
        return SideEffectMode.BROKER_MUTATION_ATTEMPTED


class RateLimitSettings(TradingConfigModel):
    """Client-side rate limit settings."""

    max_requests: int = Field(default=10, gt=0)
    per_seconds: Decimal = Field(default=Decimal("1.0"), gt=0)
    burst: int = Field(default=10, gt=0)


class TimeoutSettings(TradingConfigModel):
    """Trading runtime timeout settings in milliseconds."""

    broker_operation_timeout_ms: int = Field(default=10_000, gt=0)
    broker_check_timeout_ms: int = Field(default=5_000, gt=0)
    shutdown_timeout_ms: int = Field(default=30_000, gt=0)


class CostBudgetSettings(TradingConfigModel):
    """Cost budget and fat-finger ceiling settings."""

    max_order_notional: Decimal = Field(default=Decimal(0), ge=0)
    max_daily_transaction_cost: Decimal = Field(default=Decimal(0), ge=0)
    currency: str = "USD"

    @model_validator(mode="after")
    def validate_currency(self) -> CostBudgetSettings:
        """Validate the budget currency code.

        Returns:
            CostBudgetSettings: Validated cost budget settings.
        """
        logger.info("Validating trading cost budget settings.")
        if len(self.currency) != CURRENCY_CODE_LENGTH or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code.")
        return self


class StalenessSettings(TradingConfigModel):
    """Staleness and TTL limits."""

    quote_ttl_ms: int = Field(default=1_000, gt=0)
    context_ttl_ms: int = Field(default=5_000, gt=0)
    broker_capability_ttl_ms: int = Field(default=60_000, gt=0)


class StoreConnectionTargets(TradingConfigModel):
    """Opaque store connection target references."""

    trade_store_ref: str
    state_store_ref: str
    audit_sink_ref: str
    idempotency_store_ref: str
    event_journal_ref: str


class BrokerCapabilityEvidence(TradingConfigModel):
    """Broker capability evidence snapshot with TTL."""

    broker_name: str
    captured_at: str
    age_ms: int = Field(ge=0)
    ttl_ms: int = Field(gt=0)
    capabilities: dict[str, bool] = Field(default_factory=dict)

    def validate_fresh(self) -> None:
        """Fail closed if capability evidence exceeds its TTL.

        Raises:
            ValueError: If the capability evidence is stale.
        """
        logger.info("Validating broker capability evidence for {}.", self.broker_name)
        if self.age_ms > self.ttl_ms:
            raise ValueError("broker capability evidence is stale.")


class TradingRuntimeConfig(TradingConfigModel):
    """Effective trading runtime configuration."""

    config_version: str = "1.0.0"
    active_broker: str
    route_settings: RouteSettings = Field(default_factory=RouteSettings)
    rate_limits: RateLimitSettings = Field(default_factory=RateLimitSettings)
    timeouts: TimeoutSettings = Field(default_factory=TimeoutSettings)
    cost_budgets: CostBudgetSettings = Field(default_factory=CostBudgetSettings)
    staleness: StalenessSettings = Field(default_factory=StalenessSettings)
    store_targets: StoreConnectionTargets
    secret_references: dict[str, SecretReference] = Field(default_factory=dict)
    broker_capability_evidence: BrokerCapabilityEvidence | None = None

    @model_validator(mode="after")
    def validate_runtime_config(self) -> TradingRuntimeConfig:
        """Validate trading runtime configuration constraints.

        Returns:
            TradingRuntimeConfig: Validated runtime configuration.

        Raises:
            ValueError: If required references are missing or malformed.
        """
        logger.info("Validating trading runtime config {}.", self.config_version)
        if not self.active_broker.strip():
            raise ValueError("active_broker must be non-empty.")
        required_refs = {"broker_credentials", "database_credentials"}
        missing = required_refs - set(self.secret_references)
        if missing:
            message = f"missing required secret references: {sorted(missing)}"
            raise ValueError(message)
        if self.broker_capability_evidence is not None:
            self.broker_capability_evidence.validate_fresh()
        return self

    def live_mutation_side_effect(self) -> SideEffectMode:
        """Return passing-gate side-effect mode from route settings.

        Returns:
            SideEffectMode: Side-effect mode for a passing live gate.
        """
        logger.info("Resolving live mutation side-effect from config.")
        return self.route_settings.passing_gate_side_effect()

    def redacted_model_dump(self) -> dict[str, object]:
        """Return a redacted configuration mapping.

        Returns:
            dict[str, object]: JSON-safe redacted configuration payload.
        """
        logger.info("Building redacted trading runtime config payload.")
        payload = self.model_dump(mode="json")
        payload["secret_references"] = {
            key: value.redacted() for key, value in self.secret_references.items()
        }
        return payload
