class _Mandate: pass

from app.services.agentic.register_roles.register_roles import RegisterRolesService


def test_close_clears_contributions() -> None:
    service = RegisterRolesService(_Mandate())  # type: ignore[arg-type]
    service.close()
    assert service._roles == {}
