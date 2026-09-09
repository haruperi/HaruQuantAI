"""Feature lifecycle for the settings/diagnostics translation gateway."""
from __future__ import annotations
from typing import TYPE_CHECKING
from app.contracts.interfaces.capabilities import OPERATE_SETTINGS_CAPABILITY
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY,BUILD_DIAGNOSTICS_CAPABILITY
from app.services.interfaces.operate_settings.config import OperateSettingsConfig,from_dict
from app.services.interfaces.operate_settings.gateway import SettingsGateway
from app.services.interfaces.operate_settings.manifest import SPEC
if TYPE_CHECKING:
 from app.kernel.context import FeatureContext
 from app.kernel.feature import FeatureSpec
class OperateSettingsFeature:
 def __init__(self,spec:FeatureSpec=SPEC)->None:self.spec=spec;self._gateway:SettingsGateway|None=None
 @property
 def gateway(self)->SettingsGateway|None:return self._gateway
 async def mount(self,context:FeatureContext,config:object)->None:
  if config is None or isinstance(config,dict):parsed=from_dict(config)
  elif isinstance(config,OperateSettingsConfig):parsed=config
  else:raise TypeError("operate-settings configuration must be a mapping, OperateSettingsConfig, or None")
  gateway=SettingsGateway(context.require(ADMINISTER_SETTINGS_CAPABILITY),parsed,context.require(BUILD_DIAGNOSTICS_CAPABILITY))
  context.register_callback(gateway.close);context.provide(OPERATE_SETTINGS_CAPABILITY,gateway);self._gateway=gateway
def feature()->OperateSettingsFeature:return OperateSettingsFeature()
