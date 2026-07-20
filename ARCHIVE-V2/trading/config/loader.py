"""Trading runtime configuration loading and reload policy."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import Field

from app.services.trading.config.models import TradingConfigModel, TradingRuntimeConfig
from app.utils.logger import logger
from app.utils.standard import canonical_json

type TradingConfigSource = Mapping[str, object] | str | Path

IMMUTABLE_RUNNING_KEYS = frozenset(
    {
        "route_settings.allow_live_mutations",
        "cost_budgets.max_order_notional",
        "active_broker",
        "route_settings.promotion_stage_assignments",
        "store_targets.trade_store_ref",
        "store_targets.state_store_ref",
        "store_targets.audit_sink_ref",
        "store_targets.idempotency_store_ref",
        "store_targets.event_journal_ref",
    }
)


class ConfigChangeEvent(TradingConfigModel):
    """Journal-ready effective configuration change event."""

    actor: str
    effective_at: str
    config_version: str
    config_hash: str
    redacted_config: dict[str, object] = Field(default_factory=dict)


def load_trading_config(source: TradingConfigSource) -> TradingRuntimeConfig:
    """Load and validate a trading runtime configuration.

    Args:
        source: Explicit mapping or config file path.

    Returns:
        TradingRuntimeConfig: Validated immutable config.

    Raises:
        ValueError: If source structure is malformed.
        OSError: If an explicit file path cannot be read.
    """
    logger.info("Loading trading runtime configuration.")
    raw_config = _read_source(source)
    return TradingRuntimeConfig.model_validate(raw_config)


def _read_source(source: TradingConfigSource) -> dict[str, object]:
    """Read a config source into a plain dictionary.

    Args:
        source: Mapping or file path.

    Returns:
        dict[str, object]: Raw config mapping.

    Raises:
        ValueError: If the source is malformed.
    """
    logger.debug("Reading trading config source.")
    if isinstance(source, Mapping):
        return dict(source)
    path = Path(source)
    with path.open(encoding="utf-8") as file:
        raw = json.load(file)
    if not isinstance(raw, dict):
        raise TypeError("trading config file must contain a JSON object.")
    return raw


def hash_effective_config(config: TradingRuntimeConfig) -> str:
    """Hash the redacted effective config.

    Args:
        config: Effective trading runtime config.

    Returns:
        str: Stable SHA-256 content hash.
    """
    logger.info("Hashing effective trading runtime config.")
    serialized = canonical_json(config.redacted_model_dump())
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_config_change_event(
    *,
    config: TradingRuntimeConfig,
    actor: str,
    effective_at: str,
) -> ConfigChangeEvent:
    """Build a journal event for an effective config change.

    Args:
        config: Effective config.
        actor: Actor applying the config.
        effective_at: Timestamp supplied by caller or injected Clock.

    Returns:
        ConfigChangeEvent: Journal-ready redacted config change event.
    """
    logger.info("Building trading config change event for actor {}.", actor)
    if not actor.strip():
        raise ValueError("actor must be non-empty.")
    return ConfigChangeEvent(
        actor=actor,
        effective_at=effective_at,
        config_version=config.config_version,
        config_hash=hash_effective_config(config),
        redacted_config=config.redacted_model_dump(),
    )


def apply_trading_config_reload(
    *,
    current: TradingRuntimeConfig,
    proposed: TradingRuntimeConfig,
    session_state: str,
    actor: str,
    effective_at: str,
) -> ConfigChangeEvent:
    """Validate hot reload policy and return the change event.

    Args:
        current: Current effective config.
        proposed: Proposed effective config.
        session_state: Current live session state.
        actor: Actor applying the reload.
        effective_at: Timestamp supplied by caller or injected Clock.

    Returns:
        ConfigChangeEvent: Journal-ready config change event.

    Raises:
        ValueError: If immutable keys change while a live session is running.
    """
    logger.info("Applying trading config reload in session state {}.", session_state)
    if session_state == "running":
        changed = _changed_immutable_keys(current, proposed)
        if changed:
            message = (
                "immutable config keys changed while session is running: "
                f"{sorted(changed)}"
            )
            raise ValueError(message)
    return build_config_change_event(
        config=proposed,
        actor=actor,
        effective_at=effective_at,
    )


def _changed_immutable_keys(
    current: TradingRuntimeConfig,
    proposed: TradingRuntimeConfig,
) -> set[str]:
    """Return immutable key paths changed between configs.

    Args:
        current: Current config.
        proposed: Proposed config.

    Returns:
        set[str]: Changed immutable key paths.
    """
    logger.debug("Checking immutable trading config keys.")
    current_payload = current.model_dump(mode="json")
    proposed_payload = proposed.model_dump(mode="json")
    changed: set[str] = set()
    for key_path in IMMUTABLE_RUNNING_KEYS:
        current_value = _get_path(current_payload, key_path)
        proposed_value = _get_path(proposed_payload, key_path)
        if current_value != proposed_value:
            changed.add(key_path)
    return changed


def _get_path(payload: dict[str, Any], key_path: str) -> object:
    """Read a dotted path from a nested mapping.

    Args:
        payload: Source mapping.
        key_path: Dotted key path.

    Returns:
        object: Path value or None.
    """
    logger.debug("Reading config path {}.", key_path)
    current: object = payload
    for part in key_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
