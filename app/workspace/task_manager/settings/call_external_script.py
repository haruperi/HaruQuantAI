"""Call external script settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Call External Script"
    automation settings. Configures script path, CLI arguments, working directory,
    and process execution timeouts.

Purpose:
    FEAT-TASK-MANAGER: Support external script execution task configuration.

Key Capabilities:
    - FR-settings-call-external-script: Read and write CallExternalScript
      configuration dictionaries with validation and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.call_external_script import (
        CallExternalScriptConfig,
        CallExternalScriptSettings,
    )

    config = CallExternalScriptSettings.load({"scriptPath": "run.py"})
    target = {}
    CallExternalScriptSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["CallExternalScriptConfig", "CallExternalScriptSettings"]


@dataclass(frozen=True, slots=True)
class CallExternalScriptConfig:
    """Immutable configuration for Call External Script task."""

    script_path: str = ""
    arguments: list[str] = field(default_factory=list)
    working_directory: str = ""
    timeout_seconds: int = 300
    fail_on_error: bool = True


class CallExternalScriptSettings:
    """Serialization and deserialization helper for CallExternalScript configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: CallExternalScriptConfig | None = None,
    ) -> CallExternalScriptConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else CallExternalScriptConfig()

        base = current or CallExternalScriptConfig()
        script = str(
            payload.get("script_path") or payload.get("scriptPath") or base.script_path
        )
        raw_args = payload.get("arguments", base.arguments)
        if isinstance(raw_args, Sequence) and not isinstance(raw_args, (str, bytes)):
            args = [str(a) for a in raw_args]
        elif isinstance(raw_args, str):
            args = raw_args.split()
        else:
            args = list(base.arguments)

        work_dir = str(
            payload.get("working_directory")
            or payload.get("workingDirectory")
            or base.working_directory
        )
        timeout = int(
            payload.get("timeout_seconds")
            or payload.get("timeoutSeconds")
            or base.timeout_seconds
        )
        fail_err = bool(
            payload.get("fail_on_error")
            if "fail_on_error" in payload
            else payload.get("failOnError", base.fail_on_error)
        )

        return CallExternalScriptConfig(
            script_path=script,
            arguments=args,
            working_directory=work_dir,
            timeout_seconds=timeout,
            fail_on_error=fail_err,
        )

    @staticmethod
    def write(target: dict[str, Any], config: CallExternalScriptConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["scriptPath"] = config.script_path
        target["arguments"] = list(config.arguments)
        target["workingDirectory"] = config.working_directory
        target["timeoutSeconds"] = config.timeout_seconds
        target["failOnError"] = config.fail_on_error

    @staticmethod
    def to_dict(config: CallExternalScriptConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
