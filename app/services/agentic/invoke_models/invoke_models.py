"""Provider-neutral structured model invocation."""
from __future__ import annotations
import asyncio, json
from decimal import Decimal
from app.contracts.agentic.model_inference import ModelInvocationRequest,ModelInvocationResult,ModelProfile,ModelRuntimeProvider,ModelUsage
from app.contracts.agentic.operations import AgenticOperationsCapability,ReadinessQuery,ReadinessStatus
from app.contracts.agentic.roles import RolesCapability
from app.contracts.orchestration.resources import AdmissionStatus,FiniteResourceProfile,ResourceAdmissionPort,ResourceAdmissionRequest

class InvokeModelsService:
    def __init__(self,roles:RolesCapability,operations:AgenticOperationsCapability,resources:ResourceAdmissionPort,max_payload_bytes:int)->None:
        self._roles=roles;self._operations=operations;self._resources=resources;self._max=max_payload_bytes;self._providers:dict[str,tuple[ModelRuntimeProvider,int]]={};self._closed=False
    async def register_provider(self,provider_id:str,provider:ModelRuntimeProvider,generation:int)->None:
        self._ensure_open()
        if generation<1 or not provider_id.strip(): raise ValueError("MODEL_PROVIDER_IDENTITY_INVALID")
        current=self._providers.get(provider_id)
        if current is not None and current[1]>generation: raise ValueError("MODEL_PROVIDER_GENERATION_STALE")
        self._providers[provider_id]=(provider,generation)
    async def invoke_model(self,request:ModelInvocationRequest)->ModelInvocationResult:
        self._ensure_open()
        role=await self._roles.resolve_role(request.role_request)
        if not role.eligible: raise PermissionError("MODEL_ROLE_NOT_ELIGIBLE")
        ready=await self._operations.readiness(ReadinessQuery(request.workspace_path,request.account_id))
        if ready.status is not ReadinessStatus.READY: raise PermissionError("MODEL_AGENTIC_NOT_READY")
        profiles=(request.profile,*request.fallbacks)
        first=request.profile
        for profile in profiles:
            if profile.task_scope!=first.task_scope or profile.privacy_region!=first.privacy_region or profile.retention_policy!=first.retention_policy: raise ValueError("MODEL_FALLBACK_SCOPE_MISMATCH")
            self._validate_profile(profile)
        encoded=json.dumps(request.payload,sort_keys=True,default=str).encode()
        if len(encoded)>self._max: raise ValueError("MODEL_INPUT_OVERSIZED")
        last_error:Exception|None=None
        for profile in profiles:
            item=self._providers.get(profile.provider_id)
            if item is None: last_error=RuntimeError("MODEL_PROVIDER_UNAVAILABLE");continue
            provider,_generation=item
            admission=await self._resources.admit(ResourceAdmissionRequest(request_id=f"model:{request.request_id}:{profile.profile_id}",owner_id="FEAT-AGT-INVOKE_MODELS",work_id=request.request_id,idempotency_key=f"model:{request.request_id}:{profile.profile_id}",profile=FiniteResourceProfile(memory_bytes=min(self._max,4*1024*1024))))
            if admission.status is not AdmissionStatus.ADMITTED or admission.lease is None: last_error=PermissionError("MODEL_RESOURCE_NOT_ADMITTED");continue
            try:
                try: result=await asyncio.wait_for(provider.invoke(profile,request.payload),timeout=profile.timeout_seconds)
                except Exception as exc: last_error=exc;continue
                if result.provider_id!=profile.provider_id or result.model_id!=profile.model_id: raise ValueError("MODEL_IDENTITY_SUBSTITUTED")
                usage=self._reconcile_usage(profile,result.usage)
                payload_bytes=json.dumps(result.payload,default=str).encode()
                if len(payload_bytes)>self._max or not isinstance(result.payload,dict): raise ValueError("MODEL_OUTPUT_INVALID")
                return ModelInvocationResult(profile.profile_id,result.provider_id,result.model_id,result.payload,usage,result.provenance_ref)
            finally:
                await self._resources.release(admission.lease.lease_id,admission.lease.generation)
        raise RuntimeError("MODEL_NO_ELIGIBLE_PROVIDER") from last_error
    def _validate_profile(self,profile:ModelProfile)->None:
        if profile.provider_id.lower() in {"latest","auto","best"} or profile.model_id.lower() in {"latest","auto","best"}: raise ValueError("MODEL_IDENTITY_FLOATING")
        if profile.max_input_tokens<0 or profile.max_output_tokens<0 or profile.max_calls<1 or not profile.max_cost.is_finite() or profile.max_cost<0 or profile.timeout_seconds<=0: raise ValueError("MODEL_PROFILE_LIMIT_INVALID")
    def _reconcile_usage(self,profile:ModelProfile,usage:ModelUsage)->ModelUsage:
        if usage.input_tokens is None or usage.output_tokens is None or usage.observed_cost is None: raise ValueError("MODEL_USAGE_MISSING")
        if usage.input_tokens<0 or usage.output_tokens<0 or usage.input_tokens>profile.max_input_tokens or usage.output_tokens>profile.max_output_tokens or not usage.observed_cost.is_finite() or usage.observed_cost<0 or usage.observed_cost>profile.max_cost: raise ValueError("MODEL_USAGE_LIMIT_EXCEEDED")
        return usage
    def _ensure_open(self)->None:
        if self._closed: raise RuntimeError("invoke-models service is closed")
    def close(self)->None:
        self._closed=True;self._providers.clear()
