from app.contracts.interfaces.operate_settings import OperateDiagnosticsRequest

def test_diagnostic_request_is_explicitly_typed()->None:
 request=OperateDiagnosticsRequest("SNAPSHOT")
 assert request.operation=="SNAPSHOT"
