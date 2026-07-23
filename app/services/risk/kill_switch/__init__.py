"""Public canonical Risk kill-switch authority and block-state API."""

from app.services.risk.kill_switch.authority import (
    apply_kill_switch_command,
    check_risk_kill_switch,
)

__all__ = ["apply_kill_switch_command", "check_risk_kill_switch"]
