from app.services.interfaces.operate_settings.gateway import _closed_failure

def test_closed_failure_is_capability_unavailable()->None:
 assert _closed_failure().code=="CAPABILITY_UNAVAILABLE"
