"""Legacy workstation-principal identity resolution evidence."""

from app.services.api.identity import accounts


def test_legacy_principal_resolves_only_exact_registered_username(monkeypatch) -> None:
    """The historical usr_ prefix maps to one exact Identity account."""
    monkeypatch.setattr(
        accounts, "read_account_identity_by_user_id", lambda *_, **__: ()
    )
    monkeypatch.setattr(
        accounts,
        "read_account_record",
        lambda username, **_: (
            ({"username": username},) if username == "haruquantai" else ()
        ),
    )

    assert (
        accounts.get_username_for_principal("usr_haruquantai", request_id="req-1")
        == "haruquantai"
    )
