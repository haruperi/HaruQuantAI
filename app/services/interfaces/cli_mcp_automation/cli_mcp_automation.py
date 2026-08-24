"""Unified CLI and MCP Automation service implementation.

Purpose:
    Wrap application services through presentation-neutral CLI and MCP
    interfaces and portable automation command manifests.

Key capabilities:
    * Execute standardized application commands uniformly across callers.
    * Provide normalized structured validation and error handling.
    * Track durable long-running operations with progress and cancellation.
    * Allow client disconnection and reconnection without aborting execution.

Python API usage:
    from app.services.interfaces.cli_mcp_automation.cli_mcp_automation import (
        CliMcpAutomationService,
    )
    from app.contracts.interfaces.models import (
        ApplicationCommandRequest,
        CommandSource,
    )

    service = CliMcpAutomationService()
    req = ApplicationCommandRequest(
        command_name="system.health",
        source=CommandSource.CLI,
    )
    result = service.delegate_application_call(req)

CLI usage:
    uv run python -m app.services.interfaces.cli_mcp_automation.cli_mcp_automation
"""

from __future__ import annotations

import datetime
import logging
import uuid
from collections.abc import Callable
from typing import override

from app.contracts.interfaces.errors import (
    CommandValidationError,
    DurableJobNotFoundError,
)
from app.contracts.interfaces.models import (
    ApplicationCommandRequest,
    ApplicationCommandResult,
    CommandSource,
    CommandStatus,
    DurableCommandRef,
    DurableJobStatus,
)
from app.contracts.interfaces.ports import AutomateCommandsCapability
from app.services.interfaces.cli_mcp_automation.config import (
    CliMcpAutomationConfig,
)

logger = logging.getLogger(__name__)


class CliMcpAutomationService(AutomateCommandsCapability):
    """Production implementation of Unified CLI and MCP Automation capabilities."""

    def __init__(self, config: CliMcpAutomationConfig | None = None) -> None:
        """Initialize the automation service.

        Args:
            config: Optional configuration instance.
        """
        self._config = config or CliMcpAutomationConfig()
        self._handlers: dict[str, Callable[[dict[str, object]], dict[str, object]]] = {}
        self._durable_jobs: dict[str, DurableCommandRef] = {}
        self._register_default_handlers()
        logger.info(
            "CliMcpAutomationService initialized with timeout=%.1fs, max_jobs=%d",
            self._config.command_timeout_seconds,
            self._config.max_durable_jobs,
        )

    def _register_default_handlers(self) -> None:
        """Register built-in system and workspace command handlers."""

        def health_handler(payload: dict[str, object]) -> dict[str, object]:
            _ = payload
            return {"status": "HEALTHY", "engine": "HaruQuantAI", "version": "1.0.0"}

        def echo_handler(payload: dict[str, object]) -> dict[str, object]:
            return {"echo": payload.get("message", "")}

        self._handlers["system.health"] = health_handler
        self._handlers["system.echo"] = echo_handler

    @override
    def register_command_handler(
        self,
        command_name: str,
        handler: Callable[[dict[str, object]], dict[str, object]],
    ) -> None:
        """Register a handler callback for an application command name.

        Args:
            command_name: Canonical registered command name string.
            handler: Callable taking payload dictionary and returning output.
        """
        name = command_name.strip()
        self._handlers[name] = handler
        logger.debug("Registered command handler for '%s'", name)

    def fr_iface_delegate_application_calls(
        self,
        request: ApplicationCommandRequest,
    ) -> ApplicationCommandResult:
        """FR-IFACE-DELEGATE_APPLICATION_CALLS: Execute command across callers.

        Args:
            request: Standardized command invocation request.

        Returns:
            ApplicationCommandResult describing status, data, and errors.
        """
        name = request.command_name.strip()
        corr_id = request.correlation_id or str(uuid.uuid4())

        if not name:
            return ApplicationCommandResult(
                command_name=name,
                status=CommandStatus.VALIDATION_FAILED,
                data=None,
                errors=("Command name cannot be empty",),
                correlation_id=corr_id,
            )

        handler = self._handlers.get(name)
        if handler is None:
            logger.warning(
                "Command '%s' not recognized from source %s",
                name,
                request.source,
            )
            return ApplicationCommandResult(
                command_name=name,
                status=CommandStatus.VALIDATION_FAILED,
                data=None,
                errors=(f"Command '{name}' is not recognized",),
                correlation_id=corr_id,
            )

        try:
            output = handler(request.payload)
            return ApplicationCommandResult(
                command_name=name,
                status=CommandStatus.SUCCESS,
                data=output,
                errors=(),
                correlation_id=corr_id,
            )
        except (CommandValidationError, ValueError) as val_exc:
            logger.warning("Command validation failure for '%s': %s", name, val_exc)
            return ApplicationCommandResult(
                command_name=name,
                status=CommandStatus.VALIDATION_FAILED,
                data=None,
                errors=(str(val_exc),),
                correlation_id=corr_id,
            )
        except Exception as exc:
            logger.exception("Command execution failure for '%s'", name)
            return ApplicationCommandResult(
                command_name=name,
                status=CommandStatus.EXECUTION_FAILED,
                data=None,
                errors=(str(exc),),
                correlation_id=corr_id,
            )

    @override
    def delegate_application_call(
        self,
        request: ApplicationCommandRequest,
    ) -> ApplicationCommandResult:
        """Execute a normalized application command across UI, CLI, or MCP callers.

        Args:
            request: Standardized command invocation request.

        Returns:
            ApplicationCommandResult describing status, data, and errors.
        """
        return self.fr_iface_delegate_application_calls(request)

    def fr_iface_track_durable_commands(
        self,
        command_name: str,
        payload: dict[str, object],
        runner_fn: Callable[[DurableCommandRef], None] | None = None,
    ) -> DurableCommandRef:
        """FR-IFACE-TRACK_DURABLE_COMMANDS: Track long-running durable command.

        Args:
            command_name: Target action or command name.
            payload: Parameter dictionary.
            runner_fn: Optional synchronous runner callable.

        Returns:
            DurableCommandRef with unique job ID and initial QUEUED state.
        """
        _ = payload
        durable_job_id = str(uuid.uuid4())
        now_str = datetime.datetime.now(datetime.UTC).isoformat()

        # Enforce memory capacity boundary
        if len(self._durable_jobs) >= self._config.max_durable_jobs:
            oldest_key = next(iter(self._durable_jobs))
            del self._durable_jobs[oldest_key]

        job_ref = DurableCommandRef(
            durable_job_id=durable_job_id,
            command_name=command_name,
            status=DurableJobStatus.QUEUED,
            progress=0.0,
            stage="Command admitted into durable execution registry",
            created_at=now_str,
            updated_at=now_str,
        )
        self._durable_jobs[durable_job_id] = job_ref
        logger.info(
            "Admitted durable command job %s for '%s'",
            durable_job_id,
            command_name,
        )

        if runner_fn is not None:
            job_ref = self.update_durable_command(
                durable_job_id,
                status=DurableJobStatus.RUNNING,
                stage="Executing runner function",
            )
            try:
                runner_fn(job_ref)
            except Exception as exc:
                self.update_durable_command(
                    durable_job_id,
                    status=DurableJobStatus.FAILED,
                    error=str(exc),
                )
                raise

        return self._durable_jobs[durable_job_id]

    @override
    def track_durable_command(
        self,
        command_name: str,
        payload: dict[str, object],
        runner_fn: Callable[[DurableCommandRef], None] | None = None,
    ) -> DurableCommandRef:
        """Admit a durable long-running CLI or MCP command and return reference.

        Args:
            command_name: Target action or command name.
            payload: Parameter dictionary.
            runner_fn: Optional synchronous runner callable.

        Returns:
            DurableCommandRef with unique job ID and initial QUEUED state.
        """
        return self.fr_iface_track_durable_commands(
            command_name=command_name,
            payload=payload,
            runner_fn=runner_fn,
        )

    @override
    def get_durable_command_status(
        self,
        durable_job_id: str,
    ) -> DurableCommandRef:
        """Query lifecycle state and progress of a durable command.

        Args:
            durable_job_id: Unique durable job UUID string.

        Returns:
            DurableCommandRef describing current status, progress, and stage.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        job = self._durable_jobs.get(durable_job_id)
        if job is None:
            raise DurableJobNotFoundError(durable_job_id=durable_job_id)
        return job

    @override
    def cancel_durable_command(
        self,
        durable_job_id: str,
    ) -> DurableCommandRef:
        """Request cooperative cancellation of an active durable command.

        Args:
            durable_job_id: Target durable job UUID string.

        Returns:
            Updated DurableCommandRef marked with cancellation requested.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        existing = self.get_durable_command_status(durable_job_id)
        now_str = datetime.datetime.now(datetime.UTC).isoformat()

        updated = DurableCommandRef(
            durable_job_id=durable_job_id,
            command_name=existing.command_name,
            status=DurableJobStatus.CANCELLED,
            progress=existing.progress,
            stage="Cancellation acknowledged by automation gateway",
            is_cancel_requested=True,
            result=existing.result,
            error="Command cancelled by caller request",
            created_at=existing.created_at,
            updated_at=now_str,
        )
        self._durable_jobs[durable_job_id] = updated
        logger.info("Durable command %s marked as CANCELLED", durable_job_id)
        return updated

    @override
    def update_durable_command(
        self,
        durable_job_id: str,
        *,
        status: DurableJobStatus | None = None,
        progress: float | None = None,
        stage: str | None = None,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> DurableCommandRef:
        """Update lifecycle state or progress of a durable command.

        Args:
            durable_job_id: Target durable job UUID string.
            status: Optional updated lifecycle state.
            progress: Optional progress float between 0.0 and 1.0.
            stage: Optional stage description.
            result: Optional completed result payload dictionary.
            error: Optional error description string.

        Returns:
            Updated DurableCommandRef.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        existing = self.get_durable_command_status(durable_job_id)
        now_str = datetime.datetime.now(datetime.UTC).isoformat()

        new_status = status if status is not None else existing.status
        new_progress = progress if progress is not None else existing.progress
        new_stage = stage if stage is not None else existing.stage
        new_res = result if result is not None else existing.result
        new_err = error if error is not None else existing.error

        updated = DurableCommandRef(
            durable_job_id=durable_job_id,
            command_name=existing.command_name,
            status=new_status,
            progress=max(0.0, min(1.0, new_progress)),
            stage=new_stage,
            is_cancel_requested=existing.is_cancel_requested,
            result=new_res,
            error=new_err,
            created_at=existing.created_at,
            updated_at=now_str,
        )
        self._durable_jobs[durable_job_id] = updated
        return updated


def _scenario_1_delegate_calls(service: CliMcpAutomationService) -> None:
    """Verify FR-IFACE-DELEGATE_APPLICATION_CALLS scenario.

    Args:
        service: Active CliMcpAutomationService instance.

    Raises:
        RuntimeError: If command delegation verification fails.
    """
    req_cli = ApplicationCommandRequest(
        command_name="system.health",
        source=CommandSource.CLI,
    )
    res_cli = service.fr_iface_delegate_application_calls(req_cli)
    if res_cli.status != CommandStatus.SUCCESS or not res_cli.data:
        msg = "FR-IFACE-DELEGATE_APPLICATION_CALLS failed for CLI source"
        raise RuntimeError(msg)

    req_ui = ApplicationCommandRequest(
        command_name="system.health",
        source=CommandSource.UI,
    )
    res_ui = service.fr_iface_delegate_application_calls(req_ui)
    if res_ui.status != CommandStatus.SUCCESS or res_ui.data != res_cli.data:
        msg = "CLI and UI output parity mismatch"
        raise RuntimeError(msg)

    print("[OK] FR-IFACE-DELEGATE_APPLICATION_CALLS: Parity verified")


def _scenario_2_track_durable_commands(
    service: CliMcpAutomationService,
) -> None:
    """Verify FR-IFACE-TRACK_DURABLE_COMMANDS scenario.

    Args:
        service: Active CliMcpAutomationService instance.

    Raises:
        RuntimeError: If durable command tracking verification fails.
    """
    expected_progress = 0.6
    job = service.fr_iface_track_durable_commands(
        command_name="simulation.backtest",
        payload={"strategy_id": "strat_42"},
    )
    if job.status != DurableJobStatus.QUEUED:
        msg = "FR-IFACE-TRACK_DURABLE_COMMANDS failed initial QUEUED status"
        raise RuntimeError(msg)

    service.update_durable_command(
        job.durable_job_id,
        status=DurableJobStatus.RUNNING,
        progress=expected_progress,
        stage="Processing simulation ticks",
    )
    running = service.get_durable_command_status(job.durable_job_id)
    if (
        running.progress != expected_progress
        or running.status != DurableJobStatus.RUNNING
    ):
        msg = "FR-IFACE-TRACK_DURABLE_COMMANDS failed progress update"
        raise RuntimeError(msg)

    cancelled = service.cancel_durable_command(job.durable_job_id)
    if (
        not cancelled.is_cancel_requested
        or cancelled.status != DurableJobStatus.CANCELLED
    ):
        msg = "FR-IFACE-TRACK_DURABLE_COMMANDS failed cancellation request"
        raise RuntimeError(msg)

    print(f"[OK] FR-IFACE-TRACK_DURABLE_COMMANDS: Job {job.durable_job_id} tracked")


def _run_usage_example() -> None:
    """Run standalone verification harness for FEAT-IFACE-AUTOMATE_COMMANDS.

    Raises:
        RuntimeError: If any scenario assertion fails.
    """
    print("=================================================================")
    print("Executing FEAT-IFACE-AUTOMATE_COMMANDS Standalone Usage Harness")
    print("=================================================================")

    config = CliMcpAutomationConfig(
        title="HaruQuantAI CLI/MCP Gateway",
        command_timeout_seconds=30.0,
    )
    service = CliMcpAutomationService(config)

    _scenario_1_delegate_calls(service)
    _scenario_2_track_durable_commands(service)

    print("\n[SUCCESS] All slice FR scenarios verified successfully!")


if __name__ == "__main__":
    _run_usage_example()
