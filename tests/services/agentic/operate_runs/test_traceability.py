from app.services.agentic.operate_runs.operate_runs import OperateRunsService


class _Persistence: pass


def test_redaction_is_pre_persistence_and_bounded() -> None:
    service = OperateRunsService(_Persistence(), 128)  # type: ignore[arg-type]
    redacted = service._redact("authorization=abc secret=xyz " + "x" * 200)
    assert "abc" not in redacted
    assert "xyz" not in redacted
    assert len(redacted) <= 128
