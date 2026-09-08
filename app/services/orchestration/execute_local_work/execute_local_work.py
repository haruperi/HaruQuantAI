"""Spawn-safe local work runtime."""

from __future__ import annotations

import asyncio
import hashlib
import multiprocessing
from multiprocessing import shared_memory
import uuid

from app.contracts.orchestration.jobs import ManageJobsCapability
from app.contracts.orchestration.local_workers import LocalWorkDescriptor, LocalWorkResult, SharedInputHandle
from app.contracts.orchestration.resources import AdmissionStatus, FiniteResourceProfile, ResourceAdmissionPort, ResourceAdmissionRequest
from app.services.orchestration.execute_local_work.worker_entrypoint import run_worker


class ExecuteLocalWorkService:
    """Own spawned processes, shared mappings, cancellation and completion fencing."""

    def __init__(self, jobs: ManageJobsCapability, resources: ResourceAdmissionPort, max_input_bytes: int, cancellation_grace_seconds: float) -> None:
        self._jobs = jobs; self._resources = resources; self._max_input = max_input_bytes; self._grace = cancellation_grace_seconds
        self._generation = 1; self._handles: dict[str, shared_memory.SharedMemory] = {}; self._active: dict[str, tuple[object, object]] = {}; self._closed = False
        self._ctx = multiprocessing.get_context("spawn")

    async def stage_input(self, content: bytes) -> SharedInputHandle:
        self._ensure_open()
        if not content or len(content) > self._max_input:
            raise ValueError("LOCAL_INPUT_SIZE_INVALID")
        shm = shared_memory.SharedMemory(create=True, size=len(content)); shm.buf[:len(content)] = content
        handle_id = f"shared-{uuid.uuid4().hex}"; self._handles[handle_id] = shm
        return SharedInputHandle(handle_id, shm.name, len(content), hashlib.sha256(content).hexdigest(), self._generation)

    async def execute(self, descriptor: LocalWorkDescriptor) -> LocalWorkResult:
        self._ensure_open()
        if descriptor.input_handle.generation != self._generation:
            raise ValueError("LOCAL_INPUT_GENERATION_STALE")
        current = await self._jobs.get_semantics(descriptor.job_id)
        if current.current_attempt.attempt_id != descriptor.attempt_id or current.current_attempt.fence != descriptor.fence:
            return LocalWorkResult(descriptor.work_id, descriptor.attempt_id, descriptor.fence, "STALE", b"", "", "JOB_FENCE_STALE")
        admission = await self._resources.admit(ResourceAdmissionRequest(
            request_id=f"local:{descriptor.work_id}", owner_id="FEAT-ORCH-EXECUTE_LOCAL_WORK", work_id=descriptor.work_id,
            idempotency_key=f"local:{descriptor.job_id}:{descriptor.attempt_id}:{descriptor.work_id}",
            profile=FiniteResourceProfile(memory_bytes=descriptor.input_handle.byte_count, worker_slots=1),
        ))
        if admission.status is not AdmissionStatus.ADMITTED or admission.lease is None:
            return LocalWorkResult(descriptor.work_id, descriptor.attempt_id, descriptor.fence, "REFUSED", b"", "", f"RESOURCE_{admission.status.value.upper()}")
        cancel = self._ctx.Event(); queue = self._ctx.Queue(maxsize=1)
        process = self._ctx.Process(target=run_worker, args=(descriptor.operation_id, descriptor.input_handle.shared_memory_name, descriptor.input_handle.byte_count, descriptor.input_handle.content_hash, descriptor.seed, cancel, queue), name=f"hq-{descriptor.work_id}")
        self._active[descriptor.work_id] = (process, cancel); process.start()
        try:
            deadline = asyncio.get_running_loop().time() + descriptor.timeout_seconds
            while process.is_alive():
                if asyncio.get_running_loop().time() >= deadline:
                    cancel.set(); await asyncio.sleep(self._grace)
                    if process.is_alive(): process.terminate()
                    process.join(timeout=0.5)
                    return LocalWorkResult(descriptor.work_id, descriptor.attempt_id, descriptor.fence, "FAILED", b"", "", "TIMEOUT")
                await asyncio.sleep(0.05)
            process.join(timeout=0.1)
            if queue.empty():
                return LocalWorkResult(descriptor.work_id, descriptor.attempt_id, descriptor.fence, "FAILED", b"", "", "WORKER_EXIT_NO_RESULT")
            status, payload, reason = queue.get_nowait()
            current = await self._jobs.get_semantics(descriptor.job_id)
            if current.current_attempt.attempt_id != descriptor.attempt_id or current.current_attempt.fence != descriptor.fence:
                return LocalWorkResult(descriptor.work_id, descriptor.attempt_id, descriptor.fence, "STALE", b"", "", "JOB_FENCE_STALE")
            return LocalWorkResult(descriptor.work_id, descriptor.attempt_id, descriptor.fence, str(status), bytes(payload), hashlib.sha256(bytes(payload)).hexdigest() if payload else "", str(reason))
        finally:
            self._active.pop(descriptor.work_id, None); queue.close(); await self._resources.release(admission.lease.lease_id, admission.lease.generation)

    async def cancel(self, work_id: str) -> bool:
        active = self._active.get(work_id)
        if active is None: return False
        process, cancel = active; cancel.set()
        await asyncio.sleep(self._grace)
        if process.is_alive(): process.terminate(); process.join(timeout=0.5)
        return True

    async def release_input(self, handle: SharedInputHandle) -> None:
        shm = self._handles.pop(handle.handle_id, None)
        if shm is None: return
        shm.close(); shm.unlink()

    def _ensure_open(self) -> None:
        if self._closed: raise RuntimeError("execute-local-work service is closed")

    async def close(self) -> None:
        if self._closed: return
        self._closed = True
        for work_id in tuple(self._active): await self.cancel(work_id)
        for shm in tuple(self._handles.values()):
            try: shm.close(); shm.unlink()
            except FileNotFoundError: pass
        self._handles.clear(); self._generation += 1
