"""Tests for Bounded Historical Network Retrieval Capability."""

import asyncio
from typing import Any
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

            async def chunk_iter() -> Any:
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

        async def chunk_iter() -> Any:
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

        async def chunk_iter() -> Any:
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

        async def chunk_iter() -> Any:
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

        async def chunk_iter() -> Any:
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


def test_source_network_checks_redirect_before_contact_and_redacts_query(
    caplog: Any,
) -> None:
    import httpx
    import pytest
    from app.host.network import SourceNetwork

    contacted = []

    def handler(request: Any) -> Any:
        contacted.append(str(request.url))
        if request.url.path == "/redirect":
            return httpx.Response(
                302, headers={"Location": "https://unlisted.invalid/"}
            )
        return httpx.Response(200, json={"rows": [1]})

    async def scenario() -> None:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        session = SourceNetwork(("https://provider.example",), client=client)
        with caplog.at_level("INFO"):
            result = await session.get(
                "https://provider.example/chart", params={"crumb": "private-value"}
            )
        assert result.json() == {"rows": [1]}
        assert "private-value" not in caplog.text
        with pytest.raises(ValueError, match="declared origins"):
            await session.get("https://provider.example/redirect")
        assert len(contacted) == 2
        assert all("unlisted.invalid" not in url for url in contacted)
        await session.close()
        assert client.is_closed

    asyncio.run(scenario())


def test_archive_spools_and_closes_without_extracting_paths() -> None:
    import asyncio
    import io
    import zipfile

    import httpx
    from app.host.network import SourceNetwork

    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("../not-extracted.dat", b"actual data")

    async def scenario() -> None:
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=content.getvalue())
            )
        )
        session = SourceNetwork(("https://example.test",), client=client)
        async with session.archive("https://example.test/data.zip") as archive:
            assert archive.members() == ("../not-extracted.dat",)
            assert archive.read("../not-extracted.dat") == b"actual data"
        with pytest.raises(ValueError, match="closed"):
            archive.read("../not-extracted.dat")
        await session.close()

    asyncio.run(scenario())


def test_owner_credentials_are_not_forwarded_to_a_different_origin() -> None:
    import httpx
    from app.host.network import SourceCredentials, SourceNetwork
    from pydantic import SecretStr

    credential = SourceCredentials(
        owner="plugin.actual",
        origin="https://first.example",
        username=SecretStr("test-user"),
        password=SecretStr("test-only"),
    )
    assert "password" not in repr(credential)
    assert credential.model_dump() == {
        "owner": "plugin.actual",
        "origin": "https://first.example",
    }
    network = HistoricalNetwork(credentials=(credential,))
    wrong = network.source_session(("https://first.example",), owner="plugin.other")
    actual = network.source_session(("https://first.example",), owner="plugin.actual")
    assert not wrong.authentication_configured
    assert actual.authentication_configured

    async def run() -> None:
        requests: list[httpx.Request] = []

        def respond(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return (
                httpx.Response(302, headers={"location": "https://second.example/data"})
                if request.url.host == "first.example"
                else httpx.Response(200)
            )

        session = SourceNetwork(
            ("https://first.example", "https://second.example"),
            client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        )
        session.configure_basic_auth("https://first.example", "test-user", "test-only")
        assert (await session.head("https://first.example/data")).status == 200
        assert requests[0].method == "HEAD"
        assert requests[0].headers.get("authorization", "").startswith("Basic ")
        assert "authorization" not in requests[1].headers
        await session.close()
        await network.aclose()
        assert not actual.authentication_configured

    asyncio.run(run())


def test_historical_redirect_is_checked_before_contact() -> None:
    import httpx

    contacts: list[str] = []

    def response(request: httpx.Request) -> httpx.Response:
        contacts.append(str(request.url))
        return httpx.Response(
            302, headers={"location": "https://untrusted.example/secret"}
        )

    async def scenario() -> None:
        network = HistoricalNetwork()
        network._client = httpx.AsyncClient(transport=httpx.MockTransport(response))
        with pytest.raises(ValueError, match="redirect URL is not allowlisted"):
            await network.get("https://cdn.strategyquantcdn.com/data/test.zip")
        assert contacts == ["https://cdn.strategyquantcdn.com/data/test.zip"]
        await network.aclose()

    asyncio.run(scenario())


def test_historical_head_has_no_response_body() -> None:
    """Source probes use HEAD and never allocate an archive-sized body."""
    import httpx

    methods: list[str] = []

    def response(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        return httpx.Response(200, content=b"fixture response that must be ignored")

    async def scenario() -> None:
        network = HistoricalNetwork(
            httpx.AsyncClient(transport=httpx.MockTransport(response))
        )
        result = await network.head("https://cdn.strategyquantcdn.com/data/test.zip")
        assert result.status == 200
        assert result.body == b""
        await network.aclose()

    asyncio.run(scenario())
    assert methods == ["HEAD"]
