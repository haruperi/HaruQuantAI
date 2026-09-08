"""Strict configuration for model invocation."""
from dataclasses import dataclass
@dataclass(frozen=True)
class InvokeModelsConfig:
    max_payload_bytes:int=1_000_000

def from_dict(raw:dict[str,object]|None)->InvokeModelsConfig:
    raw={} if raw is None else raw
    if set(raw)-{"max_payload_bytes"}: raise ValueError("unknown invoke-models config key")
    value=int(raw.get("max_payload_bytes",1_000_000))
    if not 1024<=value<=16_000_000: raise ValueError("max_payload_bytes invalid")
    return InvokeModelsConfig(value)
