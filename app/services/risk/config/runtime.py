"""Runtime policy registration and read operations for FEAT-RISK-02."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.services.risk.config.profiles import RiskConfig, compute_config_hash
from app.services.risk.contracts.enums import RiskErrorCode
from app.services.risk.contracts.errors import RiskDomainError
from app.services.risk.contracts.responses import (
    guard_risk_boundary,
    unwrap_risk_response,
)
from app.services.risk.persistence import create_policy_version, read_policy_version
from app.utils import get_logger, validate_id

logger = get_logger(__name__)

_HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


@guard_risk_boundary(
    risk_level="medium",
    read_only=False,
    modifies_database=True,
)
def register_risk_policy(
    config: object,
    *,
    effective_at: datetime,
    request_id: str,
    correlation_id: str,
) -> str:
    """Register an immutable Risk configuration under its canonical hash.

    Args:
        config: Validated RiskConfig model.
        effective_at: Aware UTC activation timestamp.
        request_id: Canonical request identifier.
        correlation_id: Canonical correlation identifier.

    Returns:
        Canonical configuration hash.

    Raises:
        TypeError: If config is not a RiskConfig.
        ValueError: If timestamps or trace IDs are invalid or storage conflicts.
    """
    if not isinstance(config, RiskConfig):
        raise TypeError("config must be a RiskConfig instance")
    if effective_at.tzinfo is None or effective_at.utcoffset() != timedelta(0):
        raise ValueError("effective_at must be aware UTC timestamp")

    clean_request_id = validate_id(request_id, expected_prefix="req")
    clean_correlation_id = validate_id(correlation_id, expected_prefix="cor")

    hash_res = compute_config_hash(config)
    config_hash = unwrap_risk_response(hash_res, operation="compute_config_hash")
    payload_json = config.model_dump_json()

    logger.info(
        "Registering Risk policy version config_hash=%s profile=%s "
        "version=%s request_id=%s correlation_id=%s",
        config_hash,
        config.profile,
        config.policy_version,
        clean_request_id,
        clean_correlation_id,
    )

    create_policy_version(
        config_hash=config_hash,
        policy_version=config.policy_version,
        profile=config.profile,
        payload_json=payload_json,
        effective_at=effective_at.isoformat(),
        request_id=clean_request_id,
        correlation_id=clean_correlation_id,
    )
    return config_hash


@guard_risk_boundary(
    risk_level="low",
    read_only=True,
)
def get_risk_policy(config_hash: str) -> RiskConfig:
    """Read one registered immutable Risk configuration by exact hash.

    Args:
        config_hash: 64-character lowercase SHA-256 hash.

    Returns:
        Reconstructed validated RiskConfig model.

    Raises:
        ValueError: If config_hash format is invalid.
        RiskDomainError: If policy version is missing or tampered.
    """
    if not isinstance(config_hash, str) or not _HASH_PATTERN.fullmatch(config_hash):
        input_length = len(config_hash) if isinstance(config_hash, str) else None
        logger.error(
            "Invalid config_hash format received input_type=%s input_length=%s",
            type(config_hash).__name__,
            input_length,
        )
        raise ValueError("config_hash must be a 64-character lowercase hex string")

    logger.info("Reading Risk policy version config_hash=%s", config_hash)
    row = read_policy_version(config_hash)
    if row is None:
        logger.warning("Risk policy version config_hash=%s not found", config_hash)
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE,
            f"policy version hash {config_hash} not found",
        )

    try:
        reconstructed = RiskConfig.model_validate_json(str(row["payload_json"]))
    except Exception as error:
        logger.warning(
            "Stored policy version payload for config_hash=%s is malformed",
            config_hash,
        )
        raise RiskDomainError(
            RiskErrorCode.INVALID_RISK_CONFIG,
            f"Stored policy version payload for config_hash={config_hash} is malformed",
        ) from error

    hash_res = compute_config_hash(reconstructed)
    recomputed_hash = unwrap_risk_response(hash_res, operation="compute_config_hash")
    if recomputed_hash != config_hash:
        logger.error(
            "Stored policy version payload hash mismatch for config_hash=%s",
            config_hash,
        )
        raise RiskDomainError(
            RiskErrorCode.INVALID_RISK_CONFIG,
            "stored policy version payload hash mismatch",
        )

    logger.info(
        "Retrieved Risk policy version config_hash=%s profile=%s",
        config_hash,
        reconstructed.profile,
    )
    return reconstructed


__all__ = ["get_risk_policy", "register_risk_policy"]
