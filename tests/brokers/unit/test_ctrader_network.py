"""cTrader lifecycle-response validation tests."""

import pytest
from app.services.brokers.contracts import BrokerEnvironment
from app.services.brokers.ctrader_session.network import (
    _expect_response,
    _validate_account_environment,
    _validate_account_response,
)
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthRes,
    ProtoOAApplicationAuthRes,
    ProtoOAErrorRes,
    ProtoOAGetAccountListByAccessTokenRes,
)


def test_lifecycle_accepts_only_the_expected_response_type() -> None:
    """Accept the exact response class required by one lifecycle step."""
    response = ProtoOAApplicationAuthRes()

    assert (
        _expect_response(
            response,
            ProtoOAApplicationAuthRes,
            step="application authentication",
        )
        is response
    )


def test_lifecycle_rejects_provider_error_without_description_leakage() -> None:
    """Reject provider error responses using only the bounded provider code."""
    response = ProtoOAErrorRes(
        errorCode="INVALID_REQUEST",
        description="sensitive provider detail",
    )

    with pytest.raises(ConnectionError, match="INVALID_REQUEST") as captured:
        _expect_response(
            response,
            ProtoOAApplicationAuthRes,
            step="application authentication",
        )

    assert "sensitive provider detail" not in str(captured.value)


def test_lifecycle_rejects_unexpected_response_type() -> None:
    """Never treat a correlated but unexpected lifecycle response as success."""
    with pytest.raises(ConnectionError, match="unexpected response"):
        _expect_response(
            ProtoOAAccountAuthRes(ctidTraderAccountId=7),
            ProtoOAApplicationAuthRes,
            step="application authentication",
        )


def test_account_discovery_requires_matching_demo_account() -> None:
    """Require both account identity and provider-reported demo classification."""
    response = ProtoOAGetAccountListByAccessTokenRes(accessToken="redacted")
    account = response.ctidTraderAccount.add()
    account.ctidTraderAccountId = 7
    account.isLive = False

    _validate_account_environment(
        response,
        account_id=7,
        environment=BrokerEnvironment.DEMO,
    )

    with pytest.raises(ConnectionError, match="unavailable"):
        _validate_account_environment(
            response,
            account_id=8,
            environment=BrokerEnvironment.DEMO,
        )


def test_account_discovery_rejects_environment_mismatch() -> None:
    """A live account cannot authenticate under configured demo policy."""
    response = ProtoOAGetAccountListByAccessTokenRes(accessToken="redacted")
    account = response.ctidTraderAccount.add()
    account.ctidTraderAccountId = 7
    account.isLive = True

    with pytest.raises(ConnectionError, match="environment mismatch"):
        _validate_account_environment(
            response,
            account_id=7,
            environment=BrokerEnvironment.DEMO,
        )


def test_account_response_requires_configured_account() -> None:
    """Authentication responses for another account fail closed."""
    response = ProtoOAAccountAuthRes(ctidTraderAccountId=8)

    with pytest.raises(ConnectionError, match="account mismatch"):
        _validate_account_response(
            response,
            account_id=7,
            step="account authentication",
        )
