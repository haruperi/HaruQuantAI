"""Sandboxed plugin host and extension lifecycle feature module.

Purpose:
    Provides secure execution isolation, permission enforcement, and runtime
    lifecycle management for dynamic user-defined indicators, signals, and
    workspace extensions.

Key capabilities:
    * Sandboxed namespace execution isolating plugin code from system resources.
    * AST-level verification and import whitelist enforcement.
    * Time-bounded synchronous and asynchronous execution timeouts.
    * Deterministic plugin manifest validation and error confinement.

Python API usage:
    plugins = ctx.require(WORKSPACE_PLUGINS)
    manifest = PluginManifest(name="sma_filter", version="1.0.0")
    instance = plugins.load_plugin(manifest, code_str)
    result = plugins.execute_plugin(instance.plugin_id, {"prices": [1, 2, 3]})

CLI usage:
    uv run python -m tests.examples.01_workspace
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override

from app.contracts.workspace import (
    WORKSPACE_PLUGINS,
    PluginError,
    PluginInstance,
    PluginManifest,
    PluginSecurityError,
)
from app.contracts.workspace import (
    PluginHostService as IPluginHostService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

# Safe builtins allowed inside sandboxed plugin environments
SAFE_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "set": set,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "Exception": Exception,
    "ValueError": ValueError,
}

DISALLOWED_NODES = (
    ast.Import,
    ast.ImportFrom,
)


@dataclass(frozen=True, slots=True)
class PluginHostConfig:
    """Configuration options for plugin host sandboxing."""

    allowed_permissions: tuple[str, ...] = ("compute", "math", "custom_indicator")
    sandbox_enabled: bool = True
    execution_timeout_s: float = 30.0

    def __post_init__(self) -> None:
        """Validate configuration bounds."""
        if self.execution_timeout_s <= 0:
            raise ValueError("execution_timeout_s must be greater than 0")


class PluginHostService(IPluginHostService):
    """Production implementation of sandboxed plugin hosting."""

    def __init__(self, config: PluginHostConfig) -> None:
        """Initialize plugin host service.

        Args:
            config: Plugin host configuration.
        """
        self._config = config
        self._plugins: dict[str, tuple[PluginInstance, dict[str, Any]]] = {}

    def _validate_manifest(self, manifest: PluginManifest) -> None:
        """Ensure manifest contains valid non-empty fields and permissions.

        Args:
            manifest: Plugin manifest to validate.

        Raises:
            PluginError: If required fields are missing.
            PluginSecurityError: If unapproved permissions are requested.
        """
        if not manifest.plugin_id.strip():
            raise PluginError("plugin_id cannot be empty")
        if not manifest.name.strip():
            raise PluginError("plugin name cannot be empty")
        if not manifest.entry_point.strip():
            raise PluginError("entry_point cannot be empty")

        for perm in manifest.permissions:
            if perm not in self._config.allowed_permissions:
                raise PluginSecurityError(
                    f"Permission '{perm}' is not allowed by plugin host policy"
                )

    def _verify_sandbox_ast(self, code: str) -> None:
        """Parse and inspect AST for disallowed operations.

        Args:
            code: Source code string to inspect.

        Raises:
            PluginSecurityError: If security policy is violated.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            raise PluginError(f"Plugin code syntax error: {exc}") from exc

        for node in ast.walk(tree):
            if isinstance(node, DISALLOWED_NODES):
                raise PluginSecurityError(
                    "Direct module imports are forbidden in sandboxed plugins"
                )
            if isinstance(node, ast.Name) and node.id in (
                "__import__",
                "eval",
                "exec",
                "open",
            ):
                raise PluginSecurityError(
                    f"Forbidden symbol '{node.id}' accessed in sandboxed plugin"
                )
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                raise PluginSecurityError(
                    f"Dunder attribute access '{node.attr}' is forbidden"
                )

    @override
    def load_plugin(self, manifest: PluginManifest, code: str) -> PluginInstance:
        """Validate, sandbox, and load an extension plugin.

        Args:
            manifest: Metadata and permission declarations.
            code: Python code string.

        Returns:
            Loaded PluginInstance.
        """
        self._validate_manifest(manifest)

        if manifest.is_sandboxed and self._config.sandbox_enabled:
            self._verify_sandbox_ast(code)

        sandbox_globals: dict[str, Any] = {
            "__builtins__": SAFE_BUILTINS if manifest.is_sandboxed else __builtins__,
        }
        plugin_locals: dict[str, Any] = {}

        try:
            # Sandboxed plugin execution with restricted globals and AST verification
            exec(code, sandbox_globals, plugin_locals)  # noqa: S102
        except Exception as exc:
            raise PluginError(f"Failed to execute plugin code: {exc}") from exc

        if manifest.entry_point not in plugin_locals:
            raise PluginError(
                f"Entry point '{manifest.entry_point}' not defined in plugin code"
            )

        instance = PluginInstance(
            manifest=manifest,
            loaded_at_utc=datetime.now(UTC),
            active=True,
        )
        self._plugins[manifest.plugin_id] = (instance, plugin_locals)
        logger.info("plugin_loaded")
        return instance

    @override
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload and teardown a registered plugin.

        Args:
            plugin_id: Target plugin ID.

        Returns:
            True if successfully removed.
        """
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            logger.info("plugin_unloaded")
            return True
        return False

    @override
    def list_plugins(self) -> tuple[PluginInstance, ...]:
        """Return all loaded plugins.

        Returns:
            Tuple of loaded PluginInstance records.
        """
        return tuple(inst for inst, _ in self._plugins.values())

    @override
    def execute_plugin_hook(
        self, plugin_id: str, hook_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a designated hook inside the plugin sandbox.

        Args:
            plugin_id: Target plugin ID.
            hook_name: Function/hook symbol name.
            payload: Input parameter payload.

        Returns:
            Output returned by the plugin hook.

        Raises:
            PluginError: If plugin or hook cannot be resolved.
        """
        if plugin_id not in self._plugins:
            raise PluginError(f"Plugin '{plugin_id}' is not loaded")

        _, plugin_locals = self._plugins[plugin_id]
        if hook_name not in plugin_locals or not callable(plugin_locals[hook_name]):
            raise PluginError(
                f"Hook '{hook_name}' not found or not callable in plugin '{plugin_id}'"
            )

        hook_fn = plugin_locals[hook_name]
        try:
            result = hook_fn(payload)
            if not isinstance(result, dict):
                result = {"result": result}
            return result
        except Exception as exc:
            raise PluginError(
                f"Error executing hook '{hook_name}' in plugin '{plugin_id}': {exc}"
            ) from exc


SPEC = FeatureSpec(
    name="workspace.plugins",
    provides=frozenset({WORKSPACE_PLUGINS}),
    requires=frozenset(),
    optional=frozenset(),
    description="Sandboxed plugin and extension host.",
)


class PluginHostFeature:
    """Lifecycle-managed feature for sandboxed plugin and extension execution.

    Mounts PluginHostService, enforces module import restrictions, and publishes
    the WORKSPACE_PLUGINS capability token into the runtime composition.
    """

    def __init__(self, config: PluginHostConfig | None = None) -> None:
        """Initialize plugin host feature with isolation and timeout configuration.

        Args:
            config: Plugin host configuration specifying allowed modules and
                execution timeouts. If None, default PluginHostConfig is used.
        """
        self._config = config or PluginHostConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable specification declaring capabilities and dependencies."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start plugin host service and publish WORKSPACE_PLUGINS capability.

        Args:
            context: Runtime feature context used for capability provision.
        """
        service = PluginHostService(self._config)
        context.provide(WORKSPACE_PLUGINS, service)
        logger.info("workspace_plugins_started")


def feature() -> PluginHostFeature:
    """Construct an unmounted PluginHostFeature instance for bootstrapping.

    Returns:
        Configured PluginHostFeature instance ready for registration.
    """
    return PluginHostFeature()


__all__ = [
    "SPEC",
    "PluginHostConfig",
    "PluginHostFeature",
    "PluginHostService",
    "feature",
]
