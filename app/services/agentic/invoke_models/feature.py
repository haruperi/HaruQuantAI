"""Lifecycle for provider-neutral model invocation."""
from typing import TYPE_CHECKING
from app.contracts.agentic.capabilities import MODEL_INFERENCE_CAPABILITY,OPERATIONS_CAPABILITY,ROLES_CAPABILITY
from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.plugins.capabilities import REGISTER_CONTRIBUTIONS_CAPABILITY
from app.services.agentic.invoke_models.config import InvokeModelsConfig,from_dict
from app.services.agentic.invoke_models.invoke_models import InvokeModelsService
from app.services.agentic.invoke_models.manifest import SPEC
if TYPE_CHECKING:
 from app.kernel.context import FeatureContext
class InvokeModelsFeature:
 spec=SPEC
 async def mount(self,context:FeatureContext,config:object)->None:
  parsed=config if isinstance(config,InvokeModelsConfig) else from_dict(config if isinstance(config,dict) or config is None else None)
  context.require(REGISTER_CONTRIBUTIONS_CAPABILITY)
  service=InvokeModelsService(context.require(ROLES_CAPABILITY),context.require(OPERATIONS_CAPABILITY),context.require(RESERVE_RESOURCES_CAPABILITY),parsed.max_payload_bytes)
  context.register_callback(service.close);context.provide(MODEL_INFERENCE_CAPABILITY,service)
def feature()->InvokeModelsFeature:return InvokeModelsFeature()
