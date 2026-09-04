#!/usr/bin/env python3
"""Typed runtime policy for HaruQuantAI Task and Goal orchestration."""

from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

RUNTIME_SCHEMA_VERSION = 3
SCHEMA_V2_MODES = frozenset({"solo", "delegate", "multi-delegate", "manual"})
SUPPORTED_MODES = frozenset(
    {
        "solo",
        "solo-headless",
        "delegate",
        "delegate-headless",
        "delegate-multi",
        "manual",
        "quick-fix",
    }
)
HEADLESS_MODES = frozenset({"solo-headless", "delegate-headless", "delegate-multi"})
IDE_MODES = frozenset({"solo", "delegate", "quick-fix"})
SCHEMA_V2_MODE_MAP = {
    "solo": "solo-headless",
    "delegate": "delegate-headless",
    "multi-delegate": "delegate-multi",
    "manual": "manual",
}
SUPPORTED_APPROVAL_POLICIES = frozenset({"interactive", "unattended"})
SUPPORTED_VENDORS = frozenset({"codex", "agy", "cline", "zai"})
SUPPORTED_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})
ROLE_NAMES = ("planner", "executor", "reviewer")


class RuntimePolicyError(RuntimeError):
    """Raised when runtime policy is missing, invalid, or contradictory."""


@dataclass(frozen=True, slots=True)
class RolePolicy:
    """One configured reasoning-role transport identity."""

    vendor: str
    brand: str
    model: str
    effort: str
    provider: str = ""
    legacy_command: tuple[str, ...] = ()

    def identity(self) -> tuple[str, str, str, str]:
        """Return the immutable native-session identity fields."""
        return (self.brand, self.model, self.effort, self.provider)


@dataclass(frozen=True, slots=True)
class UnattendedPolicy:
    """Local side effects preauthorized for one frozen run."""

    allow_execute: bool = False
    allow_local_commit: bool = False
    allow_local_merge: bool = False


@dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    """Finite high-model recovery policy after normal iteration exhaustion."""

    enabled: bool = False
    max_escalations: int = 0
    additional_iterations: int = 0
    vendor: str = "codex"
    model: str = "gpt-5.6-sol"
    effort: str = "high"


@dataclass(frozen=True, slots=True)
class RuntimePolicy:
    """Complete validated runtime policy for Task and Goal execution."""

    schema_version: int
    mode: str
    approval_policy: str
    max_iterations: int
    roles: dict[str, RolePolicy]
    unattended: UnattendedPolicy
    recovery: RecoveryPolicy
    legacy_compatibility: bool = False

    @property
    def effective_mode(self) -> str:
        """Return the canonical mode without changing legacy fingerprints."""
        if self.schema_version <= 2:
            return SCHEMA_V2_MODE_MAP.get(self.mode, self.mode)
        return self.mode

    @property
    def is_headless(self) -> bool:
        """Return whether roles run through native CLI subprocesses."""
        return self.effective_mode in HEADLESS_MODES

    @property
    def is_ide(self) -> bool:
        """Return whether the current IDE chat owns role transport."""
        return self.effective_mode in IDE_MODES

    @property
    def fingerprint(self) -> str:
        """Return a stable SHA-256 of normalized policy data."""
        payload = json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def can_preauthorize_execute(self) -> bool:
        """Return whether unattended policy may satisfy the execute gate."""
        return self.approval_policy == "unattended" and self.unattended.allow_execute

    def can_preauthorize_commit(self) -> bool:
        """Return whether unattended policy may satisfy commit and local merge."""
        return (
            self.approval_policy == "unattended"
            and self.unattended.allow_local_commit
            and self.unattended.allow_local_merge
        )

    def role_config(self, role: str, *, generation: str = "normal") -> dict[str, Any]:
        """Build the process-runner configuration for one role/generation."""
        role_key = role.lower()
        if not self.is_headless:
            raise RuntimePolicyError(
                f"Mode {self.effective_mode!r} has no process-runner role config."
            )
        if generation not in {"normal", "recovery-1"}:
            raise RuntimePolicyError(f"Unsupported session generation {generation!r}.")
        if generation == "recovery-1":
            if not self.recovery.enabled:
                raise RuntimePolicyError("Recovery generation is not enabled.")
            selected = RolePolicy(
                vendor=self.recovery.vendor,
                brand=self.recovery.vendor,
                model=self.recovery.model,
                effort=self.recovery.effort,
            )
        else:
            try:
                selected = self.roles[role_key]
            except KeyError as exc:
                raise RuntimePolicyError(
                    f"Runtime policy has no configuration for role {role_key!r}."
                ) from exc
        if selected.legacy_command and generation == "normal":
            command = list(selected.legacy_command)
        else:
            command = _session_command(
                role_key,
                selected,
                mode=self.mode if self.schema_version <= 2 else self.effective_mode,
                generation=generation,
            )
        return {
            "brand": selected.brand,
            "session_adapter": selected.brand,
            "session_continuity": "required",
            "provider": selected.provider,
            "model": selected.model,
            "effort": selected.effort,
            "command": command,
            "prompt_delivery": "file",
            "template": f"docs/templates/prompt/{role_key}.md",
            "mode": self.effective_mode,
            "generation": generation,
        }


def scope_fingerprint(payload: Any) -> str:
    """Return a stable SHA-256 for frozen Task or Goal scope data."""
    normalized = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _require_bool(section: dict[str, Any], key: str, default: bool = False) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise RuntimePolicyError(f"{key} must be a boolean.")
    return value


def _role_from_v2(role: str, raw: dict[str, Any]) -> RolePolicy:
    vendor = str(raw.get("vendor", ""))
    model = str(raw.get("model", ""))
    effort = str(raw.get("effort", ""))
    provider = str(raw.get("provider", ""))
    if vendor not in SUPPORTED_VENDORS:
        raise RuntimePolicyError(f"Role {role} has unsupported vendor {vendor!r}.")
    if not model:
        raise RuntimePolicyError(f"Role {role} requires a model.")
    if effort not in SUPPORTED_EFFORTS:
        raise RuntimePolicyError(f"Role {role} has unsupported effort {effort!r}.")
    brand = "cline" if vendor in {"cline", "zai"} else vendor
    if vendor == "zai":
        provider = "zai-coding-plan"
    if brand == "cline" and not provider:
        raise RuntimePolicyError(f"Role {role} requires a Cline provider id.")
    return RolePolicy(
        vendor=vendor,
        brand=brand,
        model=model,
        effort=effort,
        provider=provider,
    )


def _legacy_role(raw: dict[str, Any]) -> RolePolicy:
    brand = str(raw.get("brand") or raw.get("session_adapter") or "")
    command = raw.get("command", [])
    if not isinstance(command, list) or not all(
        isinstance(item, str) for item in command
    ):
        raise RuntimePolicyError("Legacy role command must be a string array.")
    return RolePolicy(
        vendor=brand,
        brand=brand,
        model=str(raw.get("model", "")),
        effort=str(raw.get("effort", "")),
        provider=str(raw.get("provider", "")),
        legacy_command=tuple(command),
    )


def _session_command(
    role: str,
    policy: RolePolicy,
    *,
    mode: str,
    generation: str,
) -> list[str]:
    command = [
        sys.executable,
        ".agents/session_runner.py",
        "--brand",
        policy.brand,
        "--role",
        role,
        "--model",
        policy.model,
        "--effort",
        policy.effort,
        "--mode",
        mode,
        "--generation",
        generation,
    ]
    if policy.provider:
        command.extend(["--provider", policy.provider])
    if policy.brand == "agy":
        command.extend(["--print-timeout", "110m"])
    command.append("{prompt}")
    return command


def _parse_versioned(raw: dict[str, Any], schema_version: int) -> RuntimePolicy:
    """Parse a schema-v2 compatibility policy or canonical schema-v3 policy."""
    mode = str(raw.get("mode", ""))
    approval_policy = str(raw.get("approval_policy", "interactive"))
    max_iterations = raw.get("max_iterations", 5)
    allowed_modes = SCHEMA_V2_MODES if schema_version == 2 else SUPPORTED_MODES
    if mode not in allowed_modes:
        raise RuntimePolicyError(f"Unsupported orchestration mode {mode!r}.")
    effective_mode = SCHEMA_V2_MODE_MAP[mode] if schema_version == 2 else mode
    if approval_policy not in SUPPORTED_APPROVAL_POLICIES:
        raise RuntimePolicyError(f"Unsupported approval policy {approval_policy!r}.")
    if effective_mode == "quick-fix" and approval_policy != "interactive":
        raise RuntimePolicyError("Quick-Fix mode requires interactive approval.")
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool):
        raise RuntimePolicyError("max_iterations must be an integer.")
    if max_iterations < 1:
        raise RuntimePolicyError("max_iterations must be positive.")

    roles_raw = raw.get("roles", {})
    if not isinstance(roles_raw, dict):
        raise RuntimePolicyError("roles must be a TOML table.")
    roles: dict[str, RolePolicy] = {}
    if effective_mode in HEADLESS_MODES:
        for role in ROLE_NAMES:
            value = roles_raw.get(role)
            if not isinstance(value, dict):
                raise RuntimePolicyError(f"Mode {mode} requires roles.{role}.")
            roles[role] = _role_from_v2(role, cast("dict[str, Any]", value))
    if (
        effective_mode == "solo-headless"
        and len({item.identity() for item in roles.values()}) != 1
    ):
        raise RuntimePolicyError(
            "Solo-headless mode requires one identical P/E/R identity."
        )
    if (
        effective_mode == "delegate-headless"
        and len({item.vendor for item in roles.values()}) != 1
    ):
        raise RuntimePolicyError(
            "Delegate-headless mode requires one vendor for all roles."
        )

    unattended_raw = raw.get("unattended", {})
    if not isinstance(unattended_raw, dict):
        raise RuntimePolicyError("unattended must be a TOML table.")
    unattended_section = cast("dict[str, Any]", unattended_raw)
    unattended = UnattendedPolicy(
        allow_execute=_require_bool(unattended_section, "allow_execute"),
        allow_local_commit=_require_bool(unattended_section, "allow_local_commit"),
        allow_local_merge=_require_bool(unattended_section, "allow_local_merge"),
    )
    if approval_policy == "interactive" and any(asdict(unattended).values()):
        raise RuntimePolicyError(
            "Interactive approval cannot declare unattended permissions."
        )

    recovery_raw = raw.get("recovery", {})
    if not isinstance(recovery_raw, dict):
        raise RuntimePolicyError("recovery must be a TOML table.")
    recovery_section = cast("dict[str, Any]", recovery_raw)
    enabled = _require_bool(recovery_section, "enabled")
    max_escalations = recovery_section.get("max_escalations", 1 if enabled else 0)
    additional = recovery_section.get("additional_iterations", 1 if enabled else 0)
    if max_escalations not in ({1} if enabled else {0}):
        raise RuntimePolicyError("Recovery allows exactly one escalation when enabled.")
    if additional not in ({1} if enabled else {0}):
        raise RuntimePolicyError(
            "Recovery allows exactly one additional iteration when enabled."
        )
    recovery = RecoveryPolicy(
        enabled=enabled,
        max_escalations=int(max_escalations),
        additional_iterations=int(additional),
        vendor=str(recovery_section.get("vendor", "codex")),
        model=str(recovery_section.get("model", "gpt-5.6-sol")),
        effort=str(recovery_section.get("effort", "high")),
    )
    if enabled and approval_policy != "unattended":
        raise RuntimePolicyError("Automatic recovery is valid only in unattended mode.")
    if enabled and effective_mode not in HEADLESS_MODES:
        raise RuntimePolicyError("Automatic recovery requires a headless mode.")
    if enabled and (
        recovery.vendor,
        recovery.model,
        recovery.effort,
    ) != ("codex", "gpt-5.6-sol", "high"):
        raise RuntimePolicyError("Recovery identity must be codex/gpt-5.6-sol/high.")

    return RuntimePolicy(
        schema_version=schema_version,
        mode=mode,
        approval_policy=approval_policy,
        max_iterations=max_iterations,
        roles=roles,
        unattended=unattended,
        recovery=recovery,
    )


def load_runtime_policy(
    path: Path,
    *,
    legacy_roles: dict[str, dict[str, Any]],
    default_max_iterations: int,
) -> RuntimePolicy:
    """Load schema v3, compatible schema v2, or bounded legacy input."""
    if not path.exists():
        raise RuntimePolicyError(
            f"Workflow runtime policy is missing: {path}. Run .agents/configure.py."
        )
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    schema = raw.get("schema_version")
    if schema is None:
        mode = str(raw.get("mode", "UNCONFIGURED"))
        if mode not in SCHEMA_V2_MODES:
            raise RuntimePolicyError(f"Unsupported legacy mode {mode!r}.")
        roles = {role: _legacy_role(config) for role, config in legacy_roles.items()}
        return RuntimePolicy(
            schema_version=1,
            mode=mode,
            approval_policy="interactive",
            max_iterations=default_max_iterations,
            roles=roles,
            unattended=UnattendedPolicy(),
            recovery=RecoveryPolicy(),
            legacy_compatibility=True,
        )
    if schema not in {2, RUNTIME_SCHEMA_VERSION}:
        raise RuntimePolicyError(
            f"Unsupported runtime schema {schema!r}; expected 2 or "
            f"{RUNTIME_SCHEMA_VERSION}."
        )
    return _parse_versioned(raw, int(schema))


__all__ = [
    "HEADLESS_MODES",
    "IDE_MODES",
    "ROLE_NAMES",
    "RUNTIME_SCHEMA_VERSION",
    "RecoveryPolicy",
    "RolePolicy",
    "RuntimePolicy",
    "RuntimePolicyError",
    "UnattendedPolicy",
    "load_runtime_policy",
    "scope_fingerprint",
]
