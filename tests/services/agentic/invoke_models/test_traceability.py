from decimal import Decimal
import pytest
from app.contracts.agentic.model_inference import ModelProfile,ModelUsage
from app.services.agentic.invoke_models.invoke_models import InvokeModelsService

def test_profile_and_usage_are_finite()->None:
 service=object.__new__(InvokeModelsService)
 profile=ModelProfile("p","provider","model", "d",100,50,1,Decimal("1"),5.0,"research","local","none")
 assert InvokeModelsService._reconcile_usage(service,profile,ModelUsage(10,5,Decimal("0.1"))).observed_cost==Decimal("0.1")
 with pytest.raises(ValueError,match="MISSING"): InvokeModelsService._reconcile_usage(service,profile,ModelUsage(None,5,None))
