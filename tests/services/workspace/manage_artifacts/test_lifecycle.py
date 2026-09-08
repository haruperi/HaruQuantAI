from app.services.workspace.manage_artifacts.manage_artifacts import ManageArtifactsService


class _Persistence: pass
class _Resources: pass


def test_close_is_idempotent() -> None:
    service = ManageArtifactsService(_Persistence(), _Resources())  # type: ignore[arg-type]
    service.close()
    service.close()
    assert service._closed is True
