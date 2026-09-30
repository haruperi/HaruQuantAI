"""Tests for Bounded Historical Network Retrieval Capability."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.host.network import (
    DEFAULT_USER_AGENT,
    MAX_RESPONSE_BYTES,
    HistoricalNetwork,
)


def test_origin_allowlist_validation() -> None:
    """HistoricalNetwork enforces strict allowed origins, schemes, ports, and structures."""
    network = HistoricalNetwork()

    # Valid URLs
    valid_urls = [
        "http://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5",
        "https://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5",
        "https://cdn.strategyquantcdn.com/data/dukascopy/m1/EURUSD/metadata.dat",
        "https://cdn005.strategyquantcdn.com/data/dukascopy/m1/EURUSD/metadata.dat",
    ]
    for url in valid_urls:
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_stream = MagicMock()
            mock_client.stream.return_value.__aenter__.return_value = mock_stream
            mock_stream.status_code = 200
            mock_stream.history = ()
            mock_stream.url = url

            async def chunk_iter():
                yield b"data"

            mock_stream.aiter_bytes = chunk_iter

            res = asyncio.run(network.get(url))
            assert res.status == 200
            assert res.body == b"data"

    # Disallowed: HTTP on CDN origins
    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(network.get("http://cdn.strategyquantcdn.com/data/test.dat"))

    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(network.get("http://cdn005.strategyquantcdn.com/data/test.dat"))

    # Disallowed: Unknown origins
    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(network.get("https://example.com/test.dat"))

    # Disallowed: Credentials
    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(
            network.get(
                "http://user:pass@datafeed.dukascopy.com/datafeed/EURUSD.bi5"  # pragma: allowlist secret
            )
        )

    # Disallowed: Query params
    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(
            network.get("http://datafeed.dukascopy.com/datafeed/EURUSD.bi5?download=1")
        )

    # Disallowed: Fragments
    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(
            network.get("http://datafeed.dukascopy.com/datafeed/EURUSD.bi5#section")
        )

    # Disallowed: Custom ports
    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(
            network.get("http://datafeed.dukascopy.com:8080/datafeed/EURUSD.bi5")
        )
    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(
            network.get("https://datafeed.dukascopy.com:8443/datafeed/EURUSD.bi5")
        )


def test_user_agent_header_and_multiblock_streaming() -> None:
    """HistoricalNetwork injects browser User-Agent and completely buffers multi-block streams."""
    network = HistoricalNetwork()
    url = (
        "http://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5"
    )

    chunks = [b"chunk1_", b"chunk2_", b"chunk3"]

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_stream = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_stream
        mock_stream.status_code = 200
        mock_stream.history = ()
        mock_stream.url = url

        async def chunk_iter():
            for c in chunks:
                yield c

        mock_stream.aiter_bytes = chunk_iter

        result = asyncio.run(network.get(url))

        # Verify client was initialized with User-Agent header
        mock_client_cls.assert_called_once()
        headers_passed = mock_client_cls.call_args[1].get("headers", {})
        assert headers_passed.get("User-Agent") == DEFAULT_USER_AGENT

        # Verify all blocks were joined
        assert result.status == 200
        assert result.body == b"chunk1_chunk2_chunk3"


def test_response_size_limit_exceeded() -> None:
    """HistoricalNetwork raises ValueError when streamed payload exceeds 16MB bound."""
    network = HistoricalNetwork()
    url = (
        "http://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5"
    )

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_stream = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_stream
        mock_stream.status_code = 200
        mock_stream.history = ()
        mock_stream.url = url

        oversized_chunk = b"X" * (MAX_RESPONSE_BYTES + 1024)

        async def chunk_iter():
            yield oversized_chunk

        mock_stream.aiter_bytes = chunk_iter

        with pytest.raises(ValueError, match="response exceeds limit"):
            asyncio.run(network.get(url))


def test_rate_limit_and_error_status_handling() -> None:
    """HistoricalNetwork returns non-200 status on final attempt or 404 missing."""
    network = HistoricalNetwork()
    url = (
        "http://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5"
    )

    # 404 Not Found returns status 404 with empty bytes immediately
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_stream = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_stream
        mock_stream.status_code = 404
        mock_stream.history = ()
        mock_stream.url = url

        result = asyncio.run(network.get(url))
        assert result.status == 404
        assert result.body == b""

    # 429 retries and returns final 429 when still rate-limited
    with (
        patch("httpx.AsyncClient") as mock_client_cls,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_stream = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_stream
        mock_stream.status_code = 429
        mock_stream.history = ()
        mock_stream.url = url

        result = asyncio.run(network.get(url))
        assert result.status == 429
        assert result.body == b""
        assert mock_client.stream.call_count == 3
        assert mock_sleep.call_count == 2


def test_redirect_validation_allowlisted_and_disallowed() -> None:
    """HistoricalNetwork validates redirect target origins against allowlist."""
    network = HistoricalNetwork()
    url = (
        "http://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5"
    )

    # Allowlisted redirect target: succeeds
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_stream = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_stream
        mock_stream.status_code = 200
        mock_stream.history = [MagicMock()]
        mock_stream.url = "https://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5"

        async def chunk_iter():
            yield b"redirected_content"

        mock_stream.aiter_bytes = chunk_iter

        result = asyncio.run(network.get(url))
        assert result.status == 200
        assert result.body == b"redirected_content"

    # Non-allowlisted redirect target: raises ValueError
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_stream = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_stream
        mock_stream.status_code = 200
        mock_stream.history = [MagicMock()]
        mock_stream.url = "https://malicious.example.com/evil.bi5"

        with pytest.raises(ValueError, match="redirect URL is not allowlisted"):
            asyncio.run(network.get(url))


def test_transport_timeout_handling() -> None:
    """HistoricalNetwork retries on ConnectTimeout and raises transport unavailable."""
    import httpx

    network = HistoricalNetwork()
    url = (
        "http://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5"
    )

    with (
        patch("httpx.AsyncClient") as mock_client_cls,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.stream.side_effect = httpx.ConnectTimeout("connection timed out")

        with pytest.raises(ValueError, match="transport unavailable"):
            asyncio.run(network.get(url))

        assert mock_client.stream.call_count == 3
        assert mock_sleep.call_count == 2


def test_persistent_connection_reuse_and_aclose() -> None:
    """HistoricalNetwork reuses the same AsyncClient instance across calls and closes it cleanly."""
    network = HistoricalNetwork()
    url = (
        "http://datafeed.dukascopy.com/datafeed/EURUSD/2023/04/01/BID_candles_min_1.bi5"
    )

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_stream = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_stream
        mock_stream.status_code = 200
        mock_stream.history = ()
        mock_stream.url = url

        async def chunk_iter():
            yield b"data"

        mock_stream.aiter_bytes = chunk_iter

        # First request instantiates the client
        res1 = asyncio.run(network.get(url))
        assert res1.status == 200
        assert mock_client_cls.call_count == 1

        # Second request reuses the client without re-instantiation
        res2 = asyncio.run(network.get(url))
        assert res2.status == 200
        assert mock_client_cls.call_count == 1

        # aclose() releases the client
        asyncio.run(network.aclose())
        assert network._client is None
