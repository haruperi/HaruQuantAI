from app.utils import ExternalServiceError, map_exception


def test_map_exception_never_leaks_raw_provider_error() -> None:
    raw = RuntimeError("provider password=hunter2")
    assert map_exception(raw) == {
        "code": "INTERNAL_ERROR",
        "detail": "UNEXPECTED_EXCEPTION",
    }


def test_map_exception_preserves_symbolic_shared_evidence() -> None:
    error = ExternalServiceError("BROKER_FAILED", "TIMEOUT")
    assert map_exception(error) == {"code": "BROKER_FAILED", "detail": "TIMEOUT"}
