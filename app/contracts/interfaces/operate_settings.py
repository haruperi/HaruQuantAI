"""Public Interfaces contract for settings and bounded diagnostics translation."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import OperateSettingsRequest, OperateSettingsSuccess
from app.contracts.workspace.build_diagnostics import BenchmarkComparison,BenchmarkMeasurement,DiagnosticSnapshot,ProviderDiagnostic
from app.contracts.workspace.models import DiagnosticBundleRef

@dataclass(frozen=True, slots=True)
class OperateDiagnosticsRequest:
    operation:str
    workspace_path:Path|None=None
    providers:tuple[ProviderDiagnostic,...]=()
    target:BenchmarkMeasurement|None=None
    measurement:BenchmarkMeasurement|None=None
    include_logs:bool=True

OperateDiagnosticsResult=DiagnosticSnapshot|BenchmarkComparison|DiagnosticBundleRef|InterfaceFailure

@runtime_checkable
class OperateSettingsCapability(Protocol):
    async def administer_settings(self,request:OperateSettingsRequest)->OperateSettingsSuccess|InterfaceFailure: ...
    async def diagnostics(self,request:OperateDiagnosticsRequest)->OperateDiagnosticsResult: ...

__all__=["OperateDiagnosticsRequest","OperateDiagnosticsResult","OperateSettingsCapability"]
