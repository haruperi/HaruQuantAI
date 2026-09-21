"""Functional tests for headless command automator."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.services.gateway.application import ApplicationConfig, ApplicationService
from app.services.gateway.command_automator import (
    CommandAutomationConfig,
    CommandAutomationService,
)


def test_command_execution_dispatch() -> None:
    """Test dispatching individual CLI commands with fail-closed safety."""
    app_service = ApplicationService(ApplicationConfig())
    service = CommandAutomationService(app_service, CommandAutomationConfig())

    async def _test() -> None:
        # Empty and comment lines
        res = await service.execute_command("")
        assert res.success is True
        assert "skipped" in res.output

        res = await service.execute_command("# This is a comment")
        assert res.success is True
        assert "skipped" in res.output

        # Status command
        res = await service.execute_command("-status")
        assert res.success is True
        assert "Gateway status" in res.output

        # Info command
        res = await service.execute_command("-info")
        assert res.success is True
        assert "Gateway status" in res.output

        # Fail-closed behavior for unmounted capabilities
        res_proj = await service.execute_command("-project action=start name=Builder")
        assert res_proj.success is False
        assert "unavailable in the current runtime" in str(res_proj.error)

        res_db = await service.execute_command("-databank action=clear name=Results")
        assert res_db.success is False
        assert "unavailable in the current runtime" in str(res_db.error)

        # Unrecognized group
        res_unk = await service.execute_command("-unknown action=test")
        assert res_unk.success is False
        assert (
            res_unk.error is not None and "Unrecognized command group" in res_unk.error
        )

    asyncio.run(_test())


def test_command_token_and_jobs_dispatch(tmp_path: Path) -> None:
    """Test token creation and job dispatch when capabilities are provided."""
    from unittest.mock import MagicMock

    from app.services.gateway.authorization import (
        AuthorizationConfig,
        AuthorizationService,
    )
    from app.services.persistence.database import (
        DatabaseConfig,
        DatabaseServiceImpl,
    )
    from app.services.persistence.gateway import (
        GatewayPersistenceService,
    )

    db = DatabaseServiceImpl(DatabaseConfig(database_path=tmp_path / "cli_auth.db"))
    pers = GatewayPersistenceService(db)
    pers.initialize_schema()

    auth = AuthorizationService(
        AuthorizationConfig(token_auth_enabled=True),
        persistence=pers,
    )
    mock_jobs = MagicMock()

    app_service = ApplicationService(ApplicationConfig())
    service = CommandAutomationService(
        app_service, CommandAutomationConfig(), auth=auth, jobs=mock_jobs
    )

    async def _test() -> None:
        # 1. -token action=create
        res_tok = await service.execute_command(
            "-token action=create name=cli-operator scopes=read,write"
        )
        assert res_tok.success is True
        assert "Issued token for 'cli-operator'" in res_tok.output

        # 2. -project action=start with jobs mounted
        res_proj = await service.execute_command(
            "-project action=start name=AlphaStrategy"
        )
        assert res_proj.success is True
        assert "Submitted project job" in res_proj.output
        mock_jobs.create_job.assert_called_once()

    asyncio.run(_test())


def test_command_redirection(tmp_path: Path) -> None:
    """Test stdout redirection to file."""
    app_service = ApplicationService(ApplicationConfig())
    service = CommandAutomationService(app_service, CommandAutomationConfig())

    out_file = tmp_path / "out.txt"

    async def _test() -> None:
        res = await service.execute_command(f"-status > {out_file}")
        assert res.success is True
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "Gateway status" in content

    asyncio.run(_test())


def test_batch_file_execution(tmp_path: Path) -> None:
    """Test executing a batch file of commands and both -run and --run aliases."""
    app_service = ApplicationService(ApplicationConfig())
    service = CommandAutomationService(app_service, CommandAutomationConfig())

    batch_file = tmp_path / "commands.txt"
    batch_file.write_text(
        "# Batch test script\n-status\n\n-info\n-unknown action=fail\n",
        encoding="utf-8",
    )

    async def _test() -> None:
        results = await service.run_batch_file(batch_file)
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is True
        assert results[2].success is False

        # Run via -run command
        res1 = await service.execute_command(f"-run file={batch_file}")
        assert res1.success is False
        assert "Executed 3 batch commands. Success: False" in res1.output

        # Run via --run alias
        res2 = await service.execute_command(f"--run file={batch_file}")
        assert res2.success is False
        assert "Executed 3 batch commands. Success: False" in res2.output

        # Non-existent batch file
        missing_res = await service.run_batch_file(tmp_path / "missing.txt")
        assert len(missing_res) == 1
        assert missing_res[0].success is False
        assert missing_res[0].error is not None and "not found" in missing_res[0].error

        # -run missing file arg
        no_file_res = await service.execute_command("-run")
        assert no_file_res.success is False
        assert (
            no_file_res.error is not None
            and "Missing required 'file' argument" in no_file_res.error
        )

    asyncio.run(_test())


def test_exit_command() -> None:
    """Test exit/quit commands invoke application shutdown."""
    app_service = ApplicationService(ApplicationConfig())
    service = CommandAutomationService(app_service, CommandAutomationConfig())

    async def _test() -> None:
        res = await service.execute_command("-exit")
        assert res.success is True
        assert "Server exit requested" in res.output

    asyncio.run(_test())
