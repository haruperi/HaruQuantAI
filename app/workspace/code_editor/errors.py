"""Typed failures for the existing editor operations.

Description:
    Shares domain failures with services and the host transport adapter.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed, compatible editor failures.
Key Capabilities:
    - FR-code-editor-error-contract: Carry safe messages and host categories;
      rejection logging belongs to request/storage boundaries and is tested.
Python API Usage:
    raise CodeEditorError("Invalid editor request")
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor/test_contracts.py --no-cov
"""

from app.core.lib.errors import DomainError
from app.core.lib.responses import ErrorCode


class CodeEditorError(DomainError):
    """Compatible message-first exception with an explicit host error category."""

    category: ErrorCode

    def __init__(self, message: str, *, code: ErrorCode = ErrorCode.VALIDATION) -> None:
        """Retain existing exception construction and message formatting."""
        self.category = code
        super().__init__(code=code.value, message=message)
