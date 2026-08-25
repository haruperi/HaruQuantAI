"""Unit and acceptance tests for Unified CLI and MCP Automation (FEAT-IFACE-AUTOMATE_COMMANDS)."""

from __future__ import annotations

import pytest

from app.contracts.interfaces.errors import DurableJobNotFoundError
from app.contracts.interfaces.models import (
    ApplicationCommandRequest,
    CommandSource,
    CommandStatus,
    DurableCommandRef,
    DurableJobStatus,
)
from app.services.interfaces.cli_mcp_automation.cli_mcp_automation import (
    CliMcpAutomationService,
)
from app.services.interfaces.cli_mcp_automation.config import (
    CliMcpAutomationConfig,
)

# ============================================================================
# FR-IFACE-DELEGATE_APPLICATION_CALLS
# ============================================================================


def test_iface_delegate_application_calls() -> None:
    """Verify FR-IFACE-DELEGATE_APPLICATION_CALLS executes built-in and registered commands with caller parity."""
    service = CliMcpAutomationService()

    # 1. Built-in system.health command
    req_cli = ApplicationCommandRequest(
        command_name="system.health",
        source=CommandSource.CLI,
        correlation_id="corr-101",
    )
    res_cli = service.fr_iface_delegate_application_calls(req_cli)
    assert res_cli.status == CommandStatus.SUCCESS
    assert res_cli.data is not None
    assert res_cli.data["status"] == "HEALTHY"
    assert res_cli.data["engine"] == "HaruQuantAI"
    assert res_cli.correlation_id == "corr-101"

    # 2. Parity check: Call same command from UI and MCP sources
    req_ui = ApplicationCommandRequest(
        command_name="system.health",
        source=CommandSource.UI,
        correlation_id="corr-102",
    )
    res_ui = service.fr_iface_delegate_application_calls(req_ui)
    assert res_ui.status == CommandStatus.SUCCESS
    assert res_ui.data == res_cli.data

    req_mcp = ApplicationCommandRequest(
        command_name="system.health",
        source=CommandSource.MCP,
        correlation_id="corr-103",
    )
    res_mcp = service.delegate_application_call(req_mcp)
    assert res_mcp.status == CommandStatus.SUCCESS
    assert res_mcp.data == res_cli.data

    # 3. Custom handler registration
    def custom_strategy_compiler(
        payload: dict[str, object],
    ) -> dict[str, object]:
        strat_id = str(payload.get("strategy_id", "default"))
        return {"compiled": True, "bytecode_hash": f"hash_{strat_id}"}

    service.register_command_handler("strategy.compile", custom_strategy_compiler)

    comp_req = ApplicationCommandRequest(
        command_name="strategy.compile",
        payload={"strategy_id": "strat_999"},
        source=CommandSource.CLI,
    )
    comp_res = service.fr_iface_delegate_application_calls(comp_req)
    assert comp_res.status == CommandStatus.SUCCESS
    assert comp_res.data == {
        "compiled": True,
        "bytecode_hash": "hash_strat_999",
    }


def test_iface_delegate_application_calls_failures() -> None:
    """Verify validation and execution failure paths for application commands."""
    service = CliMcpAutomationService()

    # Empty command name
    req_empty = ApplicationCommandRequest(command_name="")
    res_empty = service.fr_iface_delegate_application_calls(req_empty)
    assert res_empty.status == CommandStatus.VALIDATION_FAILED
    assert "cannot be empty" in res_empty.errors[0]

    # Unrecognized command
    req_unknown = ApplicationCommandRequest(command_name="nonexistent.action")
    res_unknown = service.fr_iface_delegate_application_calls(req_unknown)
    assert res_unknown.status == CommandStatus.VALIDATION_FAILED
    assert "not recognized" in res_unknown.errors[0]

    # Handler raising ValueError / validation error
    def failing_validation(payload: dict[str, object]) -> dict[str, object]:
        raise ValueError("Parameter 'param_x' is required")

    service.register_command_handler("bad.param", failing_validation)
    req_bad_param = ApplicationCommandRequest(command_name="bad.param")
    res_bad_param = service.fr_iface_delegate_application_calls(req_bad_param)
    assert res_bad_param.status == CommandStatus.VALIDATION_FAILED
    assert "Parameter 'param_x' is required" in res_bad_param.errors[0]

    # Handler raising unhandled exception
    def crashing_handler(payload: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("Unexpected backend crash")

    service.register_command_handler("crash.test", crashing_handler)
    req_crash = ApplicationCommandRequest(command_name="crash.test")
    res_crash = service.fr_iface_delegate_application_calls(req_crash)
    assert res_crash.status == CommandStatus.EXECUTION_FAILED
    assert "Unexpected backend crash" in res_crash.errors[0]


# ============================================================================
# FR-IFACE-TRACK_DURABLE_COMMANDS
# ============================================================================


def test_iface_track_durable_commands() -> None:
    """Verify FR-IFACE-TRACK_DURABLE_COMMANDS tracks durable long-running jobs."""
    service = CliMcpAutomationService()

    # Submit durable command
    job = service.fr_iface_track_durable_commands(
        command_name="data.sync_history",
        payload={"symbol": "EURUSD", "timeframe": "M1"},
    )
    assert job.command_name == "data.sync_history"
    assert job.status == DurableJobStatus.QUEUED
    assert job.progress == 0.0
    assert not job.is_cancel_requested

    # Query status
    status_initial = service.get_durable_command_status(job.durable_job_id)
    assert status_initial.durable_job_id == job.durable_job_id

    # Update progress and stage
    service.update_durable_command(
        job.durable_job_id,
        status=DurableJobStatus.RUNNING,
        progress=0.45,
        stage="Downloading ticks",
    )
    status_running = service.get_durable_command_status(job.durable_job_id)
    assert status_running.status == DurableJobStatus.RUNNING
    assert status_running.progress == 0.45
    assert status_running.stage == "Downloading ticks"

    # Complete command
    service.update_durable_command(
        job.durable_job_id,
        status=DurableJobStatus.COMPLETED,
        progress=1.0,
        result={"synced_bars": 50000},
    )
    status_completed = service.get_durable_command_status(job.durable_job_id)
    assert status_completed.status == DurableJobStatus.COMPLETED
    assert status_completed.result == {"synced_bars": 50000}

    # Cancel command on separate job
    job_cancel = service.track_durable_command(
        command_name="simulation.long_run",
        payload={},
    )
    cancelled = service.cancel_durable_command(job_cancel.durable_job_id)
    assert cancelled.status == DurableJobStatus.CANCELLED
    assert cancelled.is_cancel_requested is True


def test_iface_track_durable_commands_not_found() -> None:
    """Verify querying or updating non-existent durable jobs raises DurableJobNotFoundError."""
    service = CliMcpAutomationService()

    with pytest.raises(DurableJobNotFoundError):
        service.get_durable_command_status("ghost-job-uuid")

    with pytest.raises(DurableJobNotFoundError):
        service.cancel_durable_command("ghost-job-uuid")

    with pytest.raises(DurableJobNotFoundError):
        service.update_durable_command(
            "ghost-job-uuid",
            status=DurableJobStatus.FAILED,
        )


def test_iface_track_durable_commands_with_runner() -> None:
    """Verify executing durable command with a synchronous runner function."""
    service = CliMcpAutomationService()

    def sync_runner(job_ref: DurableCommandRef) -> None:
        service.update_durable_command(
            job_ref.durable_job_id,
            status=DurableJobStatus.COMPLETED,
            progress=1.0,
            result={"output": "done"},
        )

    job = service.track_durable_command(
        command_name="runner.test",
        payload={},
        runner_fn=sync_runner,
    )
    completed = service.get_durable_command_status(job.durable_job_id)
    assert completed.status == DurableJobStatus.COMPLETED
    assert completed.progress == 1.0


def test_iface_track_durable_commands_capacity_eviction() -> None:
    """Verify FIFO eviction when max_durable_jobs capacity limit is reached."""
    service = CliMcpAutomationService(CliMcpAutomationConfig(max_durable_jobs=2))

    job1 = service.track_durable_command("cmd1", {})
    job2 = service.track_durable_command("cmd2", {})
    job3 = service.track_durable_command("cmd3", {})

    # Job 1 evicted
    with pytest.raises(DurableJobNotFoundError):
        service.get_durable_command_status(job1.durable_job_id)

    # Jobs 2 and 3 remain
    assert (
        service.get_durable_command_status(job2.durable_job_id).command_name == "cmd2"
    )
    assert (
        service.get_durable_command_status(job3.durable_job_id).command_name == "cmd3"
    )


def test_cli_mcp_automation_usage_example() -> None:
    """Verify the __main__ usage scenarios run successfully."""
    from app.services.interfaces.cli_mcp_automation.cli_mcp_automation import (
        _run_usage_example,
    )

    _run_usage_example()
