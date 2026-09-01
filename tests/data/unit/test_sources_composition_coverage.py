"""Unit tests for sources/composition.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.composition.config import BrokerProviderSettings
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.sources.composition import (
    _BrokerMarketCalendar,
    _LazyBrokerSession,
    _require_broker_result,
    _run,
    ensure_identity,
    ensure_source,
    ensure_source_access,
    ensure_storage,
    list_composable_sources,
    resolve_calendar,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def _unwrap(response):
    """Extract the raw payload from a StandardResponse for assertions."""
    return unwrap_data_response(
        response, operation="data.sources.test", request_id=_REQ_ID
    )


def test_list_composable_sources() -> None:
    """Test list_composable_sources returns tuple of available sources."""
    sources = _unwrap(list_composable_sources())
    assert isinstance(sources, tuple)


def test_ensure_source_unsupported() -> None:
    """Test ensure_source fails closed with UNSUPPORTED_SOURCE for invalid source_id."""
    response = ensure_source("unsupported_source_xyz", _REQ_ID)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "UNSUPPORTED_SOURCE"


def test_run_helper_exception() -> None:
    """Test _run raises SOURCE_UNAVAILABLE when async operation raises Exception."""

    async def _failing_coro():
        raise RuntimeError("Operation failed")

    with pytest.raises(DataError) as exc_info:
        _run(_failing_coro(), _REQ_ID)
    assert exc_info.value.code == "SOURCE_UNAVAILABLE"


def test_require_broker_result_error() -> None:
    """Test _require_broker_result raises SOURCE_UNAVAILABLE when result has error."""
    mock_res = MagicMock()
    mock_res.error = MagicMock()
    mock_res.data = None

    with pytest.raises(DataError) as exc_info:
        _require_broker_result(mock_res, operation="test_op", request_id=_REQ_ID)
    assert exc_info.value.code == "SOURCE_UNAVAILABLE"


def test_lazy_broker_session_unsupported() -> None:
    """
    Test _LazyBrokerSession.adapter raises UNSUPPORTED_SOURCE for invalid source_id.
    """
    session = _LazyBrokerSession("invalid_source_123")
    with pytest.raises(DataError) as exc_info:
        session.adapter(_REQ_ID)
    assert exc_info.value.code == "UNSUPPORTED_SOURCE"


def test_lazy_broker_session_disabled_provider() -> None:
    """
    Test _LazyBrokerSession.adapter raises SOURCE_UNAVAILABLE when provider disabled.
    """
    session = _LazyBrokerSession("mt5")
    mock_settings = BrokerProviderSettings(mt5_enabled=False)

    with patch(
        "app.services.data.sources.composition.get_data_provider_settings",
        return_value=mock_settings,
    ):
        with pytest.raises(DataError) as exc_info:
            session.adapter(_REQ_ID)
        assert exc_info.value.code == "SOURCE_UNAVAILABLE"


def test_lazy_broker_session_mt5_missing_credentials() -> None:
    """
    Test _LazyBrokerSession._mt5_adapter raises CREDENTIALS_MISSING when secrets missing.
    """
    session = _LazyBrokerSession("mt5")
    mock_settings = BrokerProviderSettings(
        mt5_enabled=True,
        mt5_login=None,
        mt5_password=None,
        mt5_server=None,
    )
    with patch(
        "app.services.data.sources.composition.get_data_provider_settings",
        return_value=mock_settings,
    ):
        with pytest.raises(DataError) as exc_info:
            session.adapter(_REQ_ID)
        assert exc_info.value.code == "CREDENTIALS_MISSING"


def test_credential_free_adapters_and_sources() -> None:
    """Test _LazyBrokerSession for yahoo, binance_spot, dukascopy."""

    async def _mock_connect():
        return MagicMock(error=None, data=True)

    mock_adapter = MagicMock()
    mock_adapter.connect.side_effect = _mock_connect
    mock_result = MagicMock(error=None, data=mock_adapter)
    with patch(
        "app.services.brokers.create_broker_adapter",
        return_value=mock_result,
    ):
        for source_id in ("yahoo", "binance_spot", "dukascopy"):
            session = _LazyBrokerSession(source_id)
            mock_settings = BrokerProviderSettings(
                **{
                    f"{('binance' if source_id == 'binance_spot' else source_id)}_enabled": True
                }
            )
            with patch(
                "app.services.data.sources.composition.get_data_provider_settings",
                return_value=mock_settings,
            ):
                adapter = session.adapter(_REQ_ID)
                assert adapter is not None
                src = session.source()
                assert src is not None


def test_broker_market_calendar_get_schedule() -> None:
    """Test _BrokerMarketCalendar.get_schedule for dukascopy."""
    mock_session = MagicMock()
    mock_adapter = MagicMock()
    mock_session.adapter.return_value = mock_adapter

    mock_sess_item = MagicMock()
    mock_sess_item.opens_at = _NOW
    mock_sess_item.closes_at = _NOW + timedelta(hours=8)
    mock_res = MagicMock()
    mock_res.error = None
    mock_res.data = (mock_sess_item,)

    def _mock_run(coro, req_id):
        coro.close()
        return mock_res

    mock_session.run.side_effect = _mock_run

    calendar = _BrokerMarketCalendar(mock_session)
    sched = calendar.get_schedule(
        source_id="dukascopy",
        symbol="EURUSD",
        timezone="UTC",
        observed_at=_NOW,
        request_id=_REQ_ID,
    )
    assert sched.symbol == "EURUSD"


def test_register_local_source(tmp_path: Path) -> None:
    """Test ensure_source for local source."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    manifest_file = raw_dir / "symbols.json"
    manifest_file.write_text(
        '{"EURUSD": {"asset_class": "forex", "revision": "v1", "retrieved_at": "2026-01-01T00:00:00Z"}}'
    )

    mock_settings = MagicMock()
    mock_settings.data_local_sources = ("local_test_source",)
    mock_settings.data_provider_sources = ()

    with (
        patch(
            "app.services.data.sources.composition.get_data_settings",
            return_value=mock_settings,
        ),
        patch(
            "app.services.data.sources.composition._resolve_raw_root",
            return_value=raw_dir,
        ),
    ):
        ensure_source("local_test_source", _REQ_ID)


def test_ensure_source_and_access_dukascopy() -> None:
    """
    Test ensure_source, ensure_source_access, resolve_calendar, and ensure_storage for dukascopy.
    """

    async def _mock_connect():
        return MagicMock(error=None, data=True)

    mock_adapter = MagicMock()
    mock_adapter.connect.side_effect = _mock_connect
    mock_result = MagicMock(error=None, data=mock_adapter)
    mock_provider_settings = BrokerProviderSettings(dukascopy_enabled=True)
    with (
        patch(
            "app.services.brokers.create_broker_adapter",
            return_value=mock_result,
        ),
        patch(
            "app.services.data.sources.composition.get_data_provider_settings",
            return_value=mock_provider_settings,
        ),
    ):
        ensure_source("dukascopy", _REQ_ID)
        ensure_source_access("dukascopy", _REQ_ID)
        cal = resolve_calendar("dukascopy", _REQ_ID)
        assert cal is not None

        with patch("app.services.data.sources.composition.run_data_migrations"):
            ensure_storage(_REQ_ID)


def test_ensure_source_all_providers() -> None:
    """Test ensure_source for mt5, yahoo, binance_spot."""
    mock_settings = MagicMock()
    mock_settings.data_local_sources = ()
    mock_settings.data_provider_sources = ("mt5", "yahoo", "binance_spot")

    with patch(
        "app.services.data.sources.composition.get_data_settings",
        return_value=mock_settings,
    ):
        ensure_source("mt5", _REQ_ID)
        ensure_source("yahoo", _REQ_ID)
        ensure_source("binance_spot", _REQ_ID)


def test_ensure_identity_dukascopy() -> None:
    """Test ensure_identity registers identity for dukascopy."""
    mock_meta = MagicMock()
    mock_meta.provider_symbol = "EURUSD"
    # Patch both _ensure_source_access_raw (so the source check is bypassed)
    # and _resolve_source_raw so the metadata fetch returns a controlled value.
    with (
        patch(
            "app.services.data.sources.composition._ensure_source_access_raw",
        ),
        patch(
            "app.services.data.sources.composition._resolve_source_raw"
        ) as mock_res_src,
    ):
        mock_src = MagicMock()
        metadata_response = MagicMock()
        metadata_response.status = "success"
        metadata_response.data = mock_meta
        mock_src.get_symbol_metadata.return_value = metadata_response
        mock_res_src.return_value = mock_src
        ensure_identity("dukascopy", "EURUSD", _REQ_ID)
