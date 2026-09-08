from app.services.agentic.operate_runs.operate_runs import OperateRunsService


class _Persistence: pass


def test_close_is_fail_closed() -> None:
    service = OperateRunsService(_Persistence(), 128)  # type: ignore[arg-type]
    service.close()
    service.close()
    assert service._closed is True
