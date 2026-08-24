"""UI domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.ui.ports import ComposeShellPresentationCapability

COMPOSE_SHELL_CAPABILITY: CapabilityKey[ComposeShellPresentationCapability] = (
    CapabilityKey(
        name="ui.compose-shell",
        major=1,
    )
)
