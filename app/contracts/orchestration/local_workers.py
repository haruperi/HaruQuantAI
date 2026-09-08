"""Public contract for bounded spawn-safe local work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class SharedInputHandle:
    handle_id: str
    shared_memory_name: str
    byte_count: int
    content_hash: str
    generation: int


@dataclass(frozen=True, slots=True)
class LocalWorkDescriptor:
    work_id: str
    job_id: str
    attempt_id: str
    fence: int
    operation_id: str
    input_handle: SharedInputHandle
    runtime_generation: int
    seed: int
    output_schema: str
    timeout_seconds: float = 30.0


@dataclass(frozen=True, slots=True)
class LocalWorkResult:
    work_id: str
    attempt_id: str
    fence: int
    status: str
    output: bytes
    output_hash: str
    reason_code: str = ""


@runtime_checkable
class LocalWorkersCapability(Protocol):
    async def stage_input(self, content: bytes) -> SharedInputHandle: ...
    async def execute(self, descriptor: LocalWorkDescriptor) -> LocalWorkResult: ...
    async def cancel(self, work_id: str) -> bool: ...
    async def release_input(self, handle: SharedInputHandle) -> None: ...


__all__ = ["LocalWorkDescriptor", "LocalWorkResult", "LocalWorkersCapability", "SharedInputHandle"]
