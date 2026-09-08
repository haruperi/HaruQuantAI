from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.contracts.agentic.roles import RoleContribution
from app.services.agentic.register_roles.register_roles import _seal


def _role() -> RoleContribution:
    return RoleContribution(
        "analyst",
        1,
        "a\r\nb",
        "in.v1",
        "out.v1",
        ("read-data",),
        "model-1",
        "limits",
        (),
        "refuse",
        "eval",
        datetime.now(timezone.utc) + timedelta(hours=1),
    )


def test_role_normalization_and_tamper_detection() -> None:
    sealed = _seal(_role())
    assert sealed.prompt_text == "a\nb"
    assert sealed.prompt_hash
    with pytest.raises(ValueError, match="PROMPT_HASH"):
        _seal(replace(sealed, prompt_text="changed"))


def test_floating_model_is_rejected() -> None:
    with pytest.raises(ValueError, match="FLOATING"):
        _seal(replace(_role(), model_profile_id="latest"))
