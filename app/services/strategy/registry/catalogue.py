"""Strategy built-in catalogue management and bootstrap operations."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.strategy.contracts.enums import (
    StrategyEnvironment,
    StrategyTimingPolicy,
)
from app.services.strategy.contracts.factories import (
    create_strategy_manifest,
    create_strategy_parameter_update_request,
    create_strategy_registration_request,
)
from app.services.strategy.contracts.policy import (
    StrategyValidationPolicy,  # noqa: TC001
)
from app.services.strategy.contracts.references import StrategyConfig, StrategyRef
from app.services.strategy.contracts.responses import (
    guard_strategy_boundary,
    unwrap_strategy_response,
)
from app.utils import get_logger

if TYPE_CHECKING:
    type AuthContext = Any

logger = get_logger(__name__)

_DEPENDENCY_HASH = "8ace32aa212299c27a9b67c9fc9b4c5f9a1fcbdc426504e88341c2766a200d60"  # pragma: allowlist secret  # noqa: E501


class _BuiltinStrategyDescriptor(BaseModel):
    """Immutable declaration for a registered Strategy built-in."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_key: str = Field(..., min_length=1)
    strategy_id: str = Field(..., min_length=1)
    strategy_version: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    strategy_class: Literal[
        "trend",
        "mean_reversion",
        "breakout",
        "structure",
        "hedging",
        "basket",
        "composite",
    ]
    module_path: str = Field(..., min_length=1)
    owner_ref: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    config_schema: Mapping[str, Any]
    default_parameters: Mapping[str, Any]
    required_indicators: tuple[str, ...]
    required_data: tuple[str, ...]
    requires_account_snapshot: bool
    source_hash: str = Field(..., min_length=64, max_length=64)
    artifact_hash: str = Field(..., min_length=64, max_length=64)
    dependency_hash: str = Field(..., min_length=64, max_length=64)


_BUILTIN_DESCRIPTORS: tuple[_BuiltinStrategyDescriptor, ...] = (
    _BuiltinStrategyDescriptor(
        evaluator_key="naive_ma_trend",
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        display_name="Naive Moving Average Trend Evaluator",
        strategy_class="trend",
        module_path="app.services.strategy.evaluators.naive_ma_trend",
        owner_ref="strategy-builtin",
        description="Single-market dual-moving-average trend follower.",
        config_schema={"type": "object", "additionalProperties": True},
        default_parameters={
            "fast_ma_period": 20,
            "slow_ma_period": 50,
            "filter_ma_period": 200,
        },
        required_indicators=("sma",),
        required_data=("EURUSD:H1",),
        requires_account_snapshot=False,
        source_hash="c4cae5c0953770f89288a5fa0a0221cea71b86fa97de2f5864ee367c699938a8",  # pragma: allowlist secret  # noqa: E501
        artifact_hash="c4cae5c0953770f89288a5fa0a0221cea71b86fa97de2f5864ee367c699938a8",  # pragma: allowlist secret  # noqa: E501
        dependency_hash=_DEPENDENCY_HASH,
    ),
    _BuiltinStrategyDescriptor(
        evaluator_key="decomposing_trade",
        strategy_id="decomposing-trade",
        strategy_version="1.0.0",
        display_name="Decomposing Trade Evaluator",
        strategy_class="mean_reversion",
        module_path="app.services.strategy.evaluators.decomposing_trade",
        owner_ref="strategy-builtin",
        description="Multi-factor trade decomposition evaluator.",
        config_schema={"type": "object", "additionalProperties": True},
        default_parameters={"rsi_period": 14, "oversold": 30, "overbought": 70},
        required_indicators=("rsi",),
        required_data=("EURUSD:H1",),
        requires_account_snapshot=False,
        source_hash="00936126fdd09467067f4c86d4b1d6209b4903cf8151a2ec0d3d059bd74562dc",  # pragma: allowlist secret  # noqa: E501
        artifact_hash="00936126fdd09467067f4c86d4b1d6209b4903cf8151a2ec0d3d059bd74562dc",  # pragma: allowlist secret  # noqa: E501
        dependency_hash=_DEPENDENCY_HASH,
    ),
    _BuiltinStrategyDescriptor(
        evaluator_key="harriet_hedging",
        strategy_id="harriet-hedging",
        strategy_version="1.0.0",
        display_name="Harriet Hedging Evaluator",
        strategy_class="hedging",
        module_path="app.services.strategy.evaluators.harriet_hedging",
        owner_ref="strategy-builtin",
        description="Deterministic delta-neutral hedging evaluator.",
        config_schema={"type": "object", "additionalProperties": True},
        default_parameters={
            "higher_timeframe": "H4",
            "lower_timeframe": "H1",
            "pip_multiplier": 10,
            "higher_min_distance_pips": 5,
            "lower_min_distance_pips": 3,
        },
        required_indicators=(),
        required_data=("EURUSD:H1",),
        requires_account_snapshot=True,
        source_hash="300d11dd59f9473dc7d6581b35b5ea102a8e937c8ec205705ddd943eef056186",  # pragma: allowlist secret  # noqa: E501
        artifact_hash="300d11dd59f9473dc7d6581b35b5ea102a8e937c8ec205705ddd943eef056186",  # pragma: allowlist secret  # noqa: E501
        dependency_hash=_DEPENDENCY_HASH,
    ),
    _BuiltinStrategyDescriptor(
        evaluator_key="market_structure",
        strategy_id="market-structure",
        strategy_version="1.0.0",
        display_name="Market Structure Evaluator",
        strategy_class="structure",
        module_path="app.services.strategy.evaluators.market_structure",
        owner_ref="strategy-builtin",
        description="Price-action market structure break evaluator.",
        config_schema={"type": "object", "additionalProperties": True},
        default_parameters={"swing_lookback": 5},
        required_indicators=("zigzag",),
        required_data=("EURUSD:H1",),
        requires_account_snapshot=False,
        source_hash="ace5228c13c6986b1c213c4fd45b3c9064eda1b2171ca001dd2147d3e6fb9d6c",  # pragma: allowlist secret  # noqa: E501
        artifact_hash="ace5228c13c6986b1c213c4fd45b3c9064eda1b2171ca001dd2147d3e6fb9d6c",  # pragma: allowlist secret  # noqa: E501
        dependency_hash=_DEPENDENCY_HASH,
    ),
    _BuiltinStrategyDescriptor(
        evaluator_key="random_walk",
        strategy_id="random-walk",
        strategy_version="1.0.0",
        display_name="Random Walk Benchmark Evaluator",
        strategy_class="composite",
        module_path="app.services.strategy.evaluators.random_walk",
        owner_ref="strategy-builtin",
        description="Stochastic random walk benchmark evaluator.",
        config_schema={"type": "object", "additionalProperties": True},
        default_parameters={
            "prob_buy": 0.5,
            "buy_magic_number": 1001,
            "sell_magic_number": 1002,
        },
        required_indicators=(),
        required_data=("EURUSD:H1",),
        requires_account_snapshot=False,
        source_hash="559e6bfc151ea470bbc1c72330c0204a0a299efddcfe15e3dbf56c9596549ece",  # pragma: allowlist secret  # noqa: E501
        artifact_hash="559e6bfc151ea470bbc1c72330c0204a0a299efddcfe15e3dbf56c9596549ece",  # pragma: allowlist secret  # noqa: E501
        dependency_hash=_DEPENDENCY_HASH,
    ),
    _BuiltinStrategyDescriptor(
        evaluator_key="sqx_breakout_atr_trailing",
        strategy_id="sqx-breakout-atr-trailing",
        strategy_version="1.0.0",
        display_name="SQX Breakout ATR Trailing Evaluator",
        strategy_class="breakout",
        module_path="app.services.strategy.evaluators.sqx_breakout_atr_trailing",
        owner_ref="strategy-builtin",
        description="Volatility breakout evaluator with ATR trailing exit.",
        config_schema={"type": "object", "additionalProperties": True},
        default_parameters={
            "breakout_lookback": 5,
            "atr_stop_period": 14,
            "stop_loss_atr_multiple": 2.0,
            "trailing_stop_atr_period": 14,
            "trailing_stop_atr_multiple": 2.0,
            "trailing_activation_atr_period": 14,
            "trailing_activation_atr_multiple": 1.5,
        },
        required_indicators=("atr",),
        required_data=("EURUSD:H1",),
        requires_account_snapshot=False,
        source_hash="faaf8474479e7696a1182fe031be9a2b0eeef9e69d2d67f8747ae61b942971f7",  # pragma: allowlist secret  # noqa: E501
        artifact_hash="faaf8474479e7696a1182fe031be9a2b0eeef9e69d2d67f8747ae61b942971f7",  # pragma: allowlist secret  # noqa: E501
        dependency_hash=_DEPENDENCY_HASH,
    ),
    _BuiltinStrategyDescriptor(
        evaluator_key="white_fairy",
        strategy_id="white-fairy",
        strategy_version="1.0.0",
        display_name="White Fairy Evaluator",
        strategy_class="basket",
        module_path="app.services.strategy.evaluators.white_fairy",
        owner_ref="strategy-builtin",
        description="Multi-symbol basket momentum evaluator.",
        config_schema={"type": "object", "additionalProperties": True},
        default_parameters={"rsi_period": 14, "oversold": 30, "overbought": 70},
        required_indicators=(),
        required_data=("EURUSD:H1", "GBPUSD:H1"),
        requires_account_snapshot=False,
        source_hash="c3bc6e97d0a92e87e6aabf7391587a422942472a9377a811e09270b39e8f52b7",  # pragma: allowlist secret  # noqa: E501
        artifact_hash="c3bc6e97d0a92e87e6aabf7391587a422942472a9377a811e09270b39e8f52b7",  # pragma: allowlist secret  # noqa: E501
        dependency_hash=_DEPENDENCY_HASH,
    ),
)


@guard_strategy_boundary
def list_builtin_strategy_descriptors() -> tuple[Mapping[str, Any], ...]:
    """List seven release-pinned built-in strategy declarations.

    Returns:
        Tuple of built-in descriptor mappings.
    """
    logger.info("Listing 7 Strategy built-in descriptors")
    return tuple(desc.model_dump() for desc in _BUILTIN_DESCRIPTORS)


@guard_strategy_boundary
def bootstrap_builtin_strategies(
    auth: object,
    policy: StrategyValidationPolicy,
    *,
    _runtime_profile: str = "RESEARCH",
) -> Mapping[str, Any]:
    """Idempotently register built-in definitions, versions, and configs.

    Args:
        auth: Caller authorization context.
        policy: Strategy validation policy.
        _runtime_profile: Optional runtime profile filter.

    Returns:
        Bootstrap summary mapping.
    """
    from app.services.strategy.registry.parameters import (
        update_strategy_parameters,
    )
    from app.services.strategy.registry.registration import (
        register_strategy_version,
    )

    logger.info("Bootstrapping 7 built-in strategies into Strategy domain database")
    registered_count = 0
    now = datetime.now(UTC)
    for idx, desc in enumerate(_BUILTIN_DESCRIPTORS, start=1):
        manifest = create_strategy_manifest(
            strategy_id=desc.strategy_id,
            strategy_version=desc.strategy_version,
            module_path=desc.module_path,
            owner_ref=desc.owner_ref,
            interface_version="v1",
            config_schema_version="v1",
            config_schema=desc.config_schema,
            required_data=desc.required_data,
            required_indicators=desc.required_indicators,
            timing_policy=StrategyTimingPolicy.EVENT_DRIVEN,
            permitted_environments=(StrategyEnvironment.RESEARCH,),
            source_hash=desc.source_hash,
            artifact_hash=desc.artifact_hash,
            dependency_hash=desc.dependency_hash,
            provenance_refs=("builtin:strategy",),
            supported_hooks=("on_bar",),
            requires_account_snapshot=desc.requires_account_snapshot,
            max_batch_records=1000,
            max_diagnostic_bytes=8192,
            max_checkpoint_bytes=65536,
            max_local_state_bytes=65536,
            decision_timeout_seconds=5.0,
        )
        reg_req = create_strategy_registration_request(
            command_id=f"cmd-00000000-0000-4000-8000-{idx:012x}",
            strategy_id=manifest.strategy_id,
            strategy_version=manifest.strategy_version,
            module_path=manifest.module_path,
            manifest=manifest,
            config_schema=manifest.config_schema,
            source_hash=manifest.source_hash,
            artifact_hash=manifest.artifact_hash,
            dependency_hash=manifest.dependency_hash,
            provenance_refs=manifest.provenance_refs,
            principal_id="builder",
            reason="bootstrap built-in strategy registration",
            lifecycle_status="APPROVED",
            authorization_ref="bootstrap-approval",
            requested_at=now,
            request_id=f"req-00000000-0000-4000-8000-{idx:012x}",
            correlation_id=f"cor-00000000-0000-4000-8000-{idx:012x}",
        )
        unwrap_strategy_response(
            register_strategy_version(reg_req, auth, policy),
            operation=f"register_strategy_version.{desc.evaluator_key}",
        )

        ref_req = StrategyRef(
            strategy_id=manifest.strategy_id,
            exact_version=manifest.strategy_version,
            environment=StrategyEnvironment.RESEARCH,
            request_id=f"req-00000000-0000-4000-8000-{idx:012x}",
            correlation_id=f"cor-00000000-0000-4000-8000-{idx:012x}",
        )
        raw_cfg = StrategyConfig(
            strategy_id=manifest.strategy_id,
            strategy_version=manifest.strategy_version,
            config_schema_version="v1",
            parameters=desc.default_parameters,
            request_id=f"req-00000000-0000-4000-8000-{idx:012x}",
        )
        param_req = create_strategy_parameter_update_request(
            command_id=f"cmd-00000000-0000-4000-8000-1000{idx:08x}",
            strategy_id=manifest.strategy_id,
            strategy_version=manifest.strategy_version,
            parameters=desc.default_parameters,
            principal_id="builder",
            reason="bootstrap built-in strategy configuration",
            ref=ref_req,
            config=raw_cfg,
            authorization_ref="bootstrap-approval",
            requested_at=now,
            request_id=f"req-00000000-0000-4000-8000-1000{idx:08x}",
            correlation_id=f"cor-00000000-0000-4000-8000-1000{idx:08x}",
        )
        unwrap_strategy_response(
            update_strategy_parameters(param_req, auth),
            operation=f"update_strategy_parameters.{desc.evaluator_key}",
        )

        registered_count += 1

    return {
        "bootstrap_status": "completed",
        "registered_strategies": registered_count,
        "configured_strategies": registered_count,
        "descriptors": tuple(desc.model_dump() for desc in _BUILTIN_DESCRIPTORS),
    }


__all__: list[str] = [
    "bootstrap_builtin_strategies",
    "list_builtin_strategy_descriptors",
]
