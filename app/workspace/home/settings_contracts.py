"""Native task-setting admission and revision validation.

Description:
    Validates task execution settings against the Core-backed Home contract and
    requires explicit edit revisions without silently accepting booleans or NaN.
Purpose:
    FEAT-HOME-SETTINGS: Preserve native task settings with explicit validation.
Key Capabilities:
    - FR-home-settings-validation: Reject invalid settings before replacement;
      isolated project tests verify unchanged files and validation logs.
Python API Usage:
    validate_settings(settings)
CLI Usage:
    uv run python -m pytest tests/workspace/home/test_project_actions.py --no-cov
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.home.contracts import ExecutionSettings

logger = get_logger(__name__)


def require_revision(revision: int) -> None:
    """Require a positive integer revision on every project mutation."""
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise DomainError(
            code="INVALID_REVISION", message="A positive integer revision is required"
        )


def validate_settings(settings: Mapping[str, Any]) -> None:
    """Admit finite native JSON and validate its execution section when present."""
    try:
        json.dumps(dict(settings), allow_nan=False)
        if "execution" in settings:
            ExecutionSettings.model_validate(settings["execution"])
    except (ValidationError, ValueError, TypeError) as error:
        raise DomainError(
            code="INVALID_SETTINGS", message="Task settings are invalid or unsupported"
        ) from error
    logger.info("FR-home-settings-validation: admitted native task settings")
