from decimal import Decimal
import pytest
from app.contracts.agentic.tool_governance import ToolDescriptor


def test_forbidden_descriptor_shape_is_explicit() -> None:
    descriptor = ToolDescriptor("x",1,"broker@1","in","out","order_execution","order_execution",("live",),"none","required",Decimal("0"),1.0,"UNTRUSTED",1)
    assert descriptor.side_effect_class == "order_execution"
