from app.services.workspace.build_diagnostics.build_diagnostics import BuildDiagnosticsService


def test_close_is_fail_closed() -> None:
    service = BuildDiagnosticsService(10, 4096); service.close(); service.close()
    assert service._closed is True
