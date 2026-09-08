from app.services.agentic.enforce_mandate.enforce_mandate import MandateService


def test_close_is_idempotent_and_fail_closed() -> None:
    service = MandateService(object(), object())
    service.close()
    service.close()
    assert service._closed is True
