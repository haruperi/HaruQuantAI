import pytest
from app.utils import SecretVersion, SecurityError, select_active_secret_version
from pydantic import SecretStr


def test_select_active_secret_version() -> None:
    versions = (
        SecretVersion("v1", SecretStr("retired")),
        SecretVersion("v2", SecretStr("active"), active=True),
    )
    active = select_active_secret_version(versions)
    assert active.version == "v2"
    assert str(active.value) == "**********"


def test_active_secret_selection_fails_closed() -> None:
    with pytest.raises(SecurityError):
        select_active_secret_version(())
    with pytest.raises(SecurityError):
        select_active_secret_version(
            (
                SecretVersion("v1", SecretStr("first"), active=True),
                SecretVersion("v2", SecretStr("second"), active=True),
            )
        )
    with pytest.raises(SecurityError):
        SecretVersion("invalid version", SecretStr("value"))
