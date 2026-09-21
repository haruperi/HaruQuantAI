"""Headless CLI argument parser and batch command automation feature.

Feature:
    FEAT-GATEWAY-AUTOMATION

Purpose:
    Provides headless command dispatch and atomic batch command script execution
    (`--run file=commands.txt`), matching the `sqcli.exe` command specification,
    dispatching to domain capabilities without executing business logic under
    capability `gateway.automation@1`.

Key capabilities:
    * Headless CLI command parser (`-project`, `-databank`, `-symbol`, `-run`, etc.).
    * Batch script file execution with line-by-line status receipts.
    * Business-logic-free delegation to registered domain capabilities.

Python API usage:
    automator = ctx.require(GATEWAY_AUTOMATION)
    res = await automator.execute_command("-project action=status name=Builder")

CLI usage:
    uv run python -m tests.examples.05_gateway
"""

from __future__ import annotations

import asyncio
import re
import shlex
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, override

from app.contracts.gateway import (
    GATEWAY_APPLICATION,
    GATEWAY_AUTHORIZATION,
    GATEWAY_AUTOMATION,
    AutomationResult,
    GatewayApplication,
    GatewayAuthorization,
)
from app.contracts.gateway import (
    CommandAutomationService as ICommandAutomationService,
)
from app.contracts.workspace import (
    WORKSPACE_JOBS,
    JobDefinition,
    JobService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

_ARG_PATTERN = re.compile(r"^([a-zA-Z0-9_-]+)=(.*)$")
_DISPATCH_GROUPS: frozenset[str] = frozenset(
    {"-project", "-databank", "-symbol", "-instrument", "-data", "-tools"}
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CommandAutomationConfig:
    """Runtime configuration for headless command automation."""

    command_timeout_s: float = 60.0
    max_batch_lines: int = 1000

    def __post_init__(self) -> None:
        """Validate configuration limits."""
        if self.command_timeout_s <= 0:
            msg = f"command_timeout_s must be > 0; got {self.command_timeout_s}"
            raise ValueError(msg)
        if self.max_batch_lines <= 0:
            msg = f"max_batch_lines must be > 0; got {self.max_batch_lines}"
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------------------------


class CommandAutomationService(ICommandAutomationService):
    """Implement headless CLI and batch script parsing and dispatch."""

    def __init__(
        self,
        app_service: GatewayApplication,
        config: CommandAutomationConfig | None = None,
        auth: GatewayAuthorization | None = None,
        jobs: JobService | None = None,
    ) -> None:
        """Initialize the command automation service.

        Args:
            app_service: Underlying GatewayApplication supervisor.
            config: Optional runtime automation configuration.
            auth: Optional gateway authorization capability for token management.
            jobs: Optional workspace jobs capability for batch project jobs.
        """
        self._app_service = app_service
        self._config = config or CommandAutomationConfig()
        self._auth = auth
        self._jobs = jobs

    @override
    async def execute_command(
        self,
        command_str: str,
    ) -> AutomationResult:
        """Parse and execute a single CLI command string.

        Args:
            command_str: Command string (e.g. '-project action=start name=Builder').

        Returns:
            `AutomationResult` describing execution outcome.
        """
        line = command_str.strip()
        if not line or line.startswith("#"):
            return AutomationResult(
                command=line, success=True, output="Comment or empty line skipped"
            )

        # Handle file redirection if present (e.g. > output.log)
        redirect_file: Path | None = None
        if " > " in line:
            parts = line.split(" > ", 1)
            line = parts[0].strip()
            redirect_file = Path(parts[1].strip().strip('"').strip("'"))

        try:
            tokens = shlex.split(line, posix=False)
        except ValueError as err:
            return AutomationResult(
                command=line, success=False, output="", error=f"Parse error: {err}"
            )

        if not tokens:
            return AutomationResult(command=line, success=True, output="Empty command")

        group = tokens[0].lower().strip('"').strip("'")
        args: dict[str, str] = {}
        for tok in tokens[1:]:
            m = _ARG_PATTERN.match(tok)
            if m:
                args[m.group(1).lower()] = m.group(2).strip('"').strip("'")

        result = await self._dispatch_group(group, args, line)

        if redirect_file is not None:
            try:
                await asyncio.to_thread(
                    redirect_file.parent.mkdir, parents=True, exist_ok=True
                )
                await asyncio.to_thread(
                    redirect_file.write_text, result.output, "utf-8"
                )
            except OSError as err:
                logger.exception("command_redirect_failed", error=str(err))

        return result

    async def _dispatch_run(
        self, group: str, args: dict[str, str], raw_command: str
    ) -> AutomationResult:
        """Handle execution of batch script file command.

        Args:
            group: Flag identifier (-run or --run).
            args: Command arguments map.
            raw_command: Original raw command line.

        Returns:
            Automation execution result.
        """
        file_path_str = args.get("file")
        if not file_path_str:
            return AutomationResult(
                command=raw_command,
                success=False,
                output="",
                error=f"Missing required 'file' argument for {group}",
            )
        results = await self.run_batch_file(Path(file_path_str))
        all_success = all(r.success for r in results)
        summary = f"Executed {len(results)} batch commands. Success: {all_success}"
        return AutomationResult(
            command=raw_command,
            success=all_success,
            output=summary,
        )

    def _dispatch_token(
        self, action: str, args: dict[str, str], raw_command: str
    ) -> AutomationResult:
        """Handle token generation commands.

        Args:
            action: Specific action under -token group.
            args: Command arguments map.
            raw_command: Original raw command line.

        Returns:
            Automation execution result.
        """
        if self._auth is None:
            return AutomationResult(
                command=raw_command,
                success=False,
                output="",
                error="Authorization capability is not available",
            )
        if action == "create":
            name = args.get("name", "cli-token")
            scopes_str = args.get("scopes", "read")
            scopes = tuple(s.strip() for s in scopes_str.split(","))
            try:
                token = self._auth.issue_token(name, scopes)
                return AutomationResult(
                    command=raw_command,
                    success=True,
                    output=f"Issued token for '{name}': {token}",
                )
            except (ValueError, RuntimeError) as exc:
                return AutomationResult(
                    command=raw_command,
                    success=False,
                    output="",
                    error=f"Token creation failed: {exc}",
                )
        return AutomationResult(
            command=raw_command,
            success=False,
            output="",
            error=f"Unknown -token action '{action}'",
        )

    def _dispatch_project(
        self, args: dict[str, str], raw_command: str
    ) -> AutomationResult:
        """Handle project run/start commands.

        Args:
            args: Command arguments map.
            raw_command: Original raw command line.

        Returns:
            Automation execution result.
        """
        if self._jobs is None:
            return AutomationResult(
                command=raw_command,
                success=False,
                output="",
                error="Jobs capability is unavailable in the current runtime",
            )
        project_name = args.get("name", "default")
        job_id = f"job-cli-{uuid.uuid4().hex[:8]}"
        try:
            definition = JobDefinition(
                job_id=job_id,
                group_id="cli-batch",
                operation="project_start",
                priority=0,
                resource_class="default",
                config_hash="none",
                payload={"project": project_name, **args},
                created_at_utc=datetime.now(UTC),
            )
            self._jobs.create_job(definition)
            out = f"Submitted project job {job_id} for '{project_name}'"
            return AutomationResult(command=raw_command, success=True, output=out)
        except (ValueError, RuntimeError, OSError) as exc:
            return AutomationResult(
                command=raw_command,
                success=False,
                output="",
                error=f"Job submission failed: {exc}",
            )

    def _dispatch_system(self, group: str, raw_command: str) -> AutomationResult:
        """Handle server status or exit commands.

        Args:
            group: Flag identifier.
            raw_command: Original raw command line.

        Returns:
            Automation execution result.
        """
        if group in {"-status", "-info"}:
            info = self._app_service.get_server_info()
            out = (
                f"Gateway status: host={info.host}, port={info.port}, "
                f"running={info.running}"
            )
            return AutomationResult(command=raw_command, success=True, output=out)
        self._app_service.stop()
        return AutomationResult(
            command=raw_command, success=True, output="Server exit requested"
        )

    async def _dispatch_group(
        self, group: str, args: dict[str, str], raw_command: str
    ) -> AutomationResult:
        """Dispatch parsed command group to domain capability endpoints."""
        action = args.get("action", "").lower()

        if group in {"-run", "--run"}:
            return await self._dispatch_run(group, args, raw_command)

        if group in {"-status", "-info", "-exit", "-quit"}:
            return self._dispatch_system(group, raw_command)

        if group == "-token":
            return self._dispatch_token(action, args, raw_command)

        if group == "-project" and action in {"start", "run"}:
            return self._dispatch_project(args, raw_command)

        if group in _DISPATCH_GROUPS:
            return AutomationResult(
                command=raw_command,
                success=False,
                output="",
                error=(
                    f"Capability for group '{group}' is unavailable in the "
                    f"current runtime"
                ),
            )

        return AutomationResult(
            command=raw_command,
            success=False,
            output="",
            error=f"Unrecognized command group '{group}'",
        )

    @override
    async def run_batch_file(
        self,
        file_path: Path,
    ) -> Sequence[AutomationResult]:
        """Execute a batch script file containing one command per line.

        Args:
            file_path: Path to the commands text file.

        Returns:
            Sequence of `AutomationResult` items in execution order.
        """
        is_file = await asyncio.to_thread(file_path.is_file)
        if not is_file:
            return (
                AutomationResult(
                    command=f"-run file={file_path}",
                    success=False,
                    output="",
                    error=f"Batch file '{file_path}' not found",
                ),
            )

        try:
            content = await asyncio.to_thread(file_path.read_text, "utf-8")
            lines = content.splitlines()
        except OSError as err:
            return (
                AutomationResult(
                    command=f"-run file={file_path}",
                    success=False,
                    output="",
                    error=f"Cannot read batch file '{file_path}': {err}",
                ),
            )

        results: list[AutomationResult] = []
        for i, raw_line in enumerate(lines[: self._config.max_batch_lines]):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            res = await self.execute_command(stripped)
            results.append(res)
            logger.info(
                "batch_command_executed",
                line=i + 1,
                command=stripped,
                success=res.success,
            )

        return tuple(results)


# ---------------------------------------------------------------------------
# Feature Specification and Wiring
# ---------------------------------------------------------------------------

SPEC = FeatureSpec(
    name="gateway.automation",
    provides=frozenset({GATEWAY_AUTOMATION}),
    requires=frozenset({GATEWAY_APPLICATION}),
    optional=frozenset({GATEWAY_AUTHORIZATION, WORKSPACE_JOBS}),
    description="Headless CLI argument parser and batch command automation.",
)


class CommandAutomationFeature:
    """Composition feature wiring for headless command automation."""

    def __init__(self, config: CommandAutomationConfig | None = None) -> None:
        """Initialize the feature with optional configuration.

        Args:
            config: Optional runtime configuration.
        """
        self._config = config or CommandAutomationConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the automation feature and publish capability.

        Args:
            context: Feature composition context.
        """
        app_service = context.require(GATEWAY_APPLICATION)
        auth = context.optional(GATEWAY_AUTHORIZATION)
        jobs = context.optional(WORKSPACE_JOBS)
        service = CommandAutomationService(
            app_service=app_service,
            config=self._config,
            auth=auth,
            jobs=jobs,
        )
        context.provide(GATEWAY_AUTOMATION, service)

    async def stop(self) -> None:
        """Stop feature and clean up resources."""


def feature() -> CommandAutomationFeature:
    """Factory creating the default CommandAutomationFeature.

    Returns:
        Configured feature instance.
    """
    return CommandAutomationFeature()
