"""Translation-only system settings and diagnostics gateway."""
from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import uuid7
from app.contracts.common.models import ProblemDetails
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import OperateSettingsRequest,OperateSettingsSuccess
from app.contracts.interfaces.operate_settings import OperateDiagnosticsRequest,OperateDiagnosticsResult
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import AdministerSettingsRequest
if TYPE_CHECKING:
 from app.contracts.workspace.administer_settings import AdministerSettingsCapability
 from app.contracts.workspace.build_diagnostics import BuildDiagnosticsCapability
 from app.services.interfaces.operate_settings.config import OperateSettingsConfig

def _failure_from_workspace(failure:WorkspaceFailure)->InterfaceFailure:
 return InterfaceFailure(request_id=failure.request_id or str(uuid7()),code="INTERFACE_VALIDATION_FAILED",problem=ProblemDetails(title=failure.problem.title,status=failure.problem.status,code=failure.code,detail=failure.problem.detail))
def _closed_failure()->InterfaceFailure:
 return InterfaceFailure(request_id=str(uuid7()),code="CAPABILITY_UNAVAILABLE",problem=ProblemDetails(title="Gateway unavailable",status=503,code="CAPABILITY_UNAVAILABLE",detail="The settings gateway is disposed."))
def _diagnostic_failure(detail:str)->InterfaceFailure:
 return InterfaceFailure(request_id=str(uuid7()),code="CAPABILITY_UNAVAILABLE",problem=ProblemDetails(title="Diagnostics unavailable",status=503,code="CAPABILITY_UNAVAILABLE",detail=detail))
class SettingsGateway:
 def __init__(self,provider:AdministerSettingsCapability,config:OperateSettingsConfig,diagnostics_provider:BuildDiagnosticsCapability|None=None)->None:
  self._provider=provider;self._config=config;self._diagnostics=diagnostics_provider;self._closed=False
 @property
 def config(self)->OperateSettingsConfig:return self._config
 async def administer_settings(self,request:OperateSettingsRequest)->OperateSettingsSuccess|InterfaceFailure:
  if self._closed:return _closed_failure()
  result=await self._provider.administer_settings(AdministerSettingsRequest(request_id=request.request_id,capability_snapshot_id=request.capability_snapshot_id,operation=request.operation,settings=request.settings,slot=request.slot,material=request.material,changed_by="system"))
  if isinstance(result,WorkspaceFailure):return _failure_from_workspace(result)
  return OperateSettingsSuccess(request_id=request.request_id,system=result.system,manifest=result.manifest,credentials=result.credentials,credential_updated=result.credential_updated,bridge=result.bridge)
 async def diagnostics(self,request:OperateDiagnosticsRequest)->OperateDiagnosticsResult:
  if self._closed:return _closed_failure()
  if self._diagnostics is None:return _diagnostic_failure("Workspace diagnostic owner is unavailable.")
  if request.operation=="SNAPSHOT":return self._diagnostics.snapshot(request.providers)
  if request.operation=="COMPARE_BENCHMARK":return self._diagnostics.compare_benchmark(request.target,request.measurement)
  if request.operation=="EXPORT":
   if request.workspace_path is None:return _diagnostic_failure("workspace_path is required for export")
   return self._diagnostics.build_diagnostic_bundle(request.workspace_path,include_logs=request.include_logs)
  return _diagnostic_failure("Unsupported diagnostic operation")
 def close(self)->None:self._closed=True
