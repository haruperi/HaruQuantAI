"""Log to file side-effect strategy action block.

Description:
    Appends message text to a designated file during strategy execution,
    supporting optional sandboxed directory containment.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-LOG-TO-FILE: Append diagnostic message text to file destination.
Python API Usage:
    from app.extend.blocks.actions.log_to_file import (
        LogToFile,
        log_to_file,
    )
    rec = log_to_file("strategy.log", "Event occurred")
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import BaseBlock
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.actions.base import ActionRecord

logger = get_logger(__name__)


class LogToFileAction(BaseBlock):
    """Action block to append diagnostic messages to a designated file.

    Discovery, import, and registration never perform filesystem I/O.
    File writing occurs strictly upon calling `execute()`.
    """

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="action.log_to_file",
        version="1.0.0",
        name="Log To File",
        description="Appends message text to a file during strategy execution",
        category="actions",
        tags=("action", "log", "file", "side_effect"),
        execution_kind=ExecutionKind.ACTION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("message", PortType.STRING, "Log message text"),
            InputPort(
                "filename",
                PortType.STRING,
                "Destination file name",
                default="strategy.log",
            ),
        ),
        outputs=(OutputPort("record", PortType.ANY, "Execution ActionRecord"),),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )

    filename: str = Field(
        default="strategy.log",
        min_length=1,
        title="Filename",
        description="Destination filename",
    )
    message: str = Field(
        default="",
        title="Message",
        description="Message content to append",
    )
    base_dir: str | None = Field(
        default=None,
        title="Base Directory",
        description="Optional base directory to sandbox output file path",
    )

    def execute(self) -> ActionRecord:
        """Execute file logging side effect.

        Returns:
            ActionRecord describing the written action details.
        """
        written_path: str | None = None
        if self.base_dir is not None:
            dir_path = Path(self.base_dir)
            dir_path.mkdir(parents=True, exist_ok=True)
            target = dir_path / self.filename
            with target.open("a", encoding="utf-8") as f:
                f.write(self.message + "\n")
            written_path = str(target)

        logger.debug(
            "FR-ACTIONS-LOG-TO-FILE: LogToFile(file='%s', msg='%s')",
            self.filename,
            self.message,
        )
        return ActionRecord(
            action_type="log_to_file",
            params={
                "filename": self.filename,
                "message": self.message,
                "path": written_path,
            },
        )


# Direct donor class alias matching SQ.Blocks.OtherActions.LogToFile
LogToFile = LogToFileAction


def log_to_file(
    filename: str = "strategy.log",
    message: str = "",
    base_dir: Path | str | None = None,
) -> ActionRecord:
    """Convenience functional invocation of LogToFileAction."""
    action = LogToFileAction(
        filename=filename,
        message=message,
        base_dir=str(base_dir) if base_dir else None,
    )
    return action.execute()


__all__ = ["LogToFile", "LogToFileAction", "log_to_file"]
