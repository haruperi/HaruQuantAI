"""Idempotent bootstrap registration for the Discretionary Manual Order strategy."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from app.services.strategy.contracts.factories import (
    create_strategy_manifest,
    create_strategy_registration_request,
    create_strategy_validation_policy,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)
from app.services.strategy.registry.registration import register_strategy_version
from app.utils import derive_stable_id, generate_id, get_logger

if TYPE_CHECKING:
    from app.services.strategy.contracts.manifest import StrategyManifest
    from app.services.strategy.contracts.policy import StrategyValidationPolicy

logger = get_logger(__name__)

STRATEGY_ID = "discretionary-manual-order"
_MODULE_PATH = "app.services.strategy.discretionary.module"
_APPROVED_MODULE_ROOT = "app.services.strategy.discretionary"
_OWNER_REF = "risk-manual-preflight"
# Trading's TradingMutationInput.route is exactly "demo" | "live"; the
# discretionary strategy only ever needs to be reachable from those routes.
_ENVIRONMENTS = ("DEMO", "LIVE")
# SHA-256 of module.py's exact byte content. Strategy source may not read the
# filesystem at runtime (see test_import_security.py), so this identity
# module's content hash is a fixed literal, matching the built-in strategy
# descriptors in registry/catalogue.py. Regenerate with
# ``hashlib.sha256(Path("module.py").read_bytes()).hexdigest()`` if module.py
# ever changes.
_MODULE_HASH = "58dc053da92a795307330b8391635e1e26bb61f5c11f60852d5d26d931b44fcc"  # pragma: allowlist secret  # noqa: E501


def get_discretionary_strategy_id() -> str:
    """Return the registered Discretionary Manual Order strategy identity.

    Returns:
        The exact immutable registered strategy identity.
    """
    return STRATEGY_ID


def strategy_version_for(environment: str) -> str:
    """Return the registered Discretionary strategy version for one environment.

    Args:
        environment: One of the registered Strategy environments (``DEMO``,
            ``LIVE``).

    Returns:
        The exact immutable registered strategy version string.
    """
    return f"1.0.0-{environment.lower()}"


def _manifest(environment: str) -> StrategyManifest:
    """Build one environment-scoped Discretionary Manual Order manifest.

    Args:
        environment: Exact single permitted Strategy environment.

    Returns:
        Validated Strategy manifest.
    """
    return create_strategy_manifest(
        strategy_id=STRATEGY_ID,
        strategy_version=strategy_version_for(environment),
        module_path=_MODULE_PATH,
        owner_ref=_OWNER_REF,
        interface_version="v1",
        config_schema_version="v1",
        config_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        required_data=(),
        required_indicators=(),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        permitted_environments=(get_strategy_environment(environment),),
        source_hash=_MODULE_HASH,
        artifact_hash=_MODULE_HASH,
        dependency_hash=_MODULE_HASH,
        provenance_refs=(f"haruquantai:{_MODULE_PATH}",),
        supported_hooks=(),
        requires_account_snapshot=True,
        max_batch_records=1,
        max_diagnostic_bytes=4096,
        max_checkpoint_bytes=4096,
        max_local_state_bytes=4096,
        decision_timeout_seconds=30,
    )


def _policy() -> StrategyValidationPolicy:
    """Build the bounded registration policy for the discretionary module root.

    Returns:
        Validated Strategy validation policy.
    """
    return create_strategy_validation_policy(
        policy_version="discretionary-v1",
        approved_module_roots=(_APPROVED_MODULE_ROOT,),
        max_config_payload_bytes=256,
        max_config_nesting_depth=2,
        max_config_string_length=64,
        max_config_collection_items=1,
    )


def register_discretionary_strategy(auth: object) -> tuple[object, ...]:
    """Idempotently register the Discretionary Manual Order strategy.

    Registers one immutable version per Trading-reachable route environment
    (``DEMO``, ``LIVE``). Safe to call on every process start: a prior
    identical registration is reported by Strategy as an ``IDEMPOTENT``
    mutation, and an already-persisted version is reported as ``REJECTED``
    with reason ``IMMUTABLE_VERSION_EXISTS`` — neither is treated as a
    failure here. Any other rejection or envelope failure raises, since it
    means the discretionary strategy is not usably registered.

    Args:
        auth: Authenticated context holding the ``strategy:register``
            permission.

    Returns:
        One registration `StandardResponse` per registered environment, in
        the same order as ``_ENVIRONMENTS``.

    Raises:
        RuntimeError: If registration fails for a reason other than the
            version already existing.
    """
    policy = _policy()
    results: list[object] = []
    for environment in _ENVIRONMENTS:
        manifest = _manifest(environment)
        # Deterministic (not generate_id-random) so a repeated bootstrap call
        # for the exact same manifest content replays idempotently instead of
        # minting a fresh command every process start.
        command_id = derive_stable_id(
            "id", f"discretionary-strategy-register:{manifest.strategy_version}"
        )
        request = create_strategy_registration_request(
            command_id=command_id,
            strategy_id=manifest.strategy_id,
            strategy_version=manifest.strategy_version,
            module_path=manifest.module_path,
            manifest=manifest,
            config_schema=manifest.config_schema,
            source_hash=manifest.source_hash,
            artifact_hash=manifest.artifact_hash,
            dependency_hash=manifest.dependency_hash,
            provenance_refs=manifest.provenance_refs,
            principal_id="system:strategy-bootstrap",
            reason="Bootstrap registration for human-initiated manual orders",
            lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
            authorization_ref="system:manual-order-preflight-bootstrap",
            requested_at=datetime.now(UTC),
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
        )
        # register_strategy_version is decorated with @guard_strategy_boundary,
        # which wraps its declared StrategyMutationResult return in a runtime
        # StandardResponse envelope (.status/.data/.error) that the decorator's
        # static type signature does not reflect.
        result = cast("Any", register_strategy_version(request, auth, policy))
        if result.status != "success" or result.data is None:
            logger.error(
                "Discretionary strategy registration envelope failed for %s: %s",
                environment,
                result.error,
            )
            envelope_message = (
                f"discretionary strategy registration failed for {environment}"
            )
            raise RuntimeError(envelope_message)
        mutation = result.data
        if (
            mutation.status == "REJECTED"
            and "IMMUTABLE_VERSION_EXISTS" not in mutation.reason_codes
        ):
            logger.error(
                "Discretionary strategy registration rejected for %s: %s",
                environment,
                mutation.reason_codes,
            )
            rejection_message = (
                f"discretionary strategy registration rejected for {environment}: "
                f"{mutation.reason_codes}"
            )
            raise RuntimeError(rejection_message)
        results.append(result)
    return tuple(results)


__all__ = [
    "get_discretionary_strategy_id",
    "register_discretionary_strategy",
    "strategy_version_for",
]
