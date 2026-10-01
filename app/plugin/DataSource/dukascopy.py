# ruff: noqa: INP001 -- approved singular plugin namespace
"""Dukascopy Acquisition Plugin, Adaptive Rate Throttling, and Feed Decoding.

Description:
    Implements the Dukascopy historical market data acquisition plugin, providing
    automated downloading, decompaction, rate throttling, and ingestion of tick
    and minute bar datasets into host Parquet storage.

    External relations and workflows:
    - Workspace attachment: Discovered and attached dynamically to
      `workspace.data_manager` under slot `data_source.acquisition`
      (`app.workspace.DataManager.workspace`).
    - Host capabilities: Requires `host.market_data` (`MarketAccess`) for
      dataset registration and partition storage, `host.network`
      (`NetworkAccess`) for HTTP chunk fetching, and `host.jobs` (`JobAccess`)
      for background task supervision, and `host.resources` (`ResourceAccess`)
      for immutable optional provider-result chunks.
    - Upstream feeds: Connects to official Dukascopy bi5 LZMA-compressed feeds
      or StrategyQuant CDN mirrors with automatic fallback.

    Internal coordination:
    - RateCorrector: Implements Source acquisition adaptive throttling (+25%
      backoff on 429/503 HTTP responses, -25% delay reduction after 100
      consecutive successes).
    - Binary decoders: `_decode_ticks` and `_decode_m1` parse big-endian binary
      bi5 blocks, adjusting for point values, volumes, and explicit UTC
      chunk boundaries.
    - Lifecycle hooks: `_prepare`, `invoke`, `close` managing operations
      (`catalog`, `definitions.add`, `add`, `download.start`, `download.status`,
      `download.cancel`, `import`, `disclaimer`, `files.list`, `delete`,
      `clear`, `rows.read`, `download.results.read`).

Purpose:
    FEAT-PLUGIN-DATASOURCE-DUKASCOPY: Automated historical market data
    acquisition from Dukascopy and CDN mirrors with adaptive throttling and
    direct Parquet ingestion.

Key Capabilities:
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-ACQUIRE: Bounded concurrent UTC acquisition.
      Associated: `run_download()`, `_direct_payload()`, `_source_archive()`.
      Logging: Logs starts/completion, HTTP fallback and unavailable chunks;
      tests verify received coverage without false publication.
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-DECODE: Source rounding and BI5 header repair.
      Associated: `_decode_ticks()`, `_decode_m1()`, `_decompress_bi5()`.
      Logging: Logs decoded symbol/row counts and rejected malformed chunks;
      source-bound tests compare canonical outputs and raw direct arrays.
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-CATALOG: Idempotent host-owned definitions.
      Associated: `add_symbol()`, `_get_symbol_info()`, `invoke()`.
      Logging: Logs registration counts, reused IDs, and catalog operations.
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-CLI: UI-equivalent authenticated commands.
      Associated: `_main()`, `_invoke()`, `_scan_market_m1()`, `_scan_market_ticks()`.
      Logging: The CLI entrypoint explicitly configures host logging; operations,
      scans, resampling and export counts are logged with redacted diagnostics.
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-LIFECYCLE: Declared capability attachment.
      Associated: `_prepare()`, `close()`.
      Logging: Logs preparation and release; host owns cancellation and custody.
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-RESULTS: Bounded immutable raw result pages.
      Associated: `_provider_table()`, `publish_result()`, `_result_frames()`.
      Logging: Logs decoded row counts and scoped resource publication/read;
      tests verify source precision, provenance, digest and cancellation retention.

Python API Usage:
    Only add_symbol, download_data and show_disclaimer are exported. The host
    discovery attribute prepare aliases internal _prepare and is excluded from
    __all__; all other module-defined functions are internal.

    ```python
    from app.plugin.DataSource.dukascopy import (
        add_symbol, download_data, show_disclaimer,
    )

    show_disclaimer()
    symbol_id = add_symbol(symbol="GBPUSD", broker="dukascopy")
    prices = download_data("GBPUSD", "2026-09-29", "2026-09-29")
    ```

CLI Usage:
    ```bash
    # Run offline deterministic usage example:
    uv run python -m tests.examples.dukascopy_offline
    # Normal app host must be running; effects match the paired UI:
    uv run python app/plugin/DataSource/dukascopy.py add-symbol \
        --symbol GBPUSD --type M1 --broker dukascopy
    uv run python -m app.plugin.DataSource.dukascopy --help
    ```
"""

from __future__ import annotations

__all__ = ["add_symbol", "download_data", "show_disclaimer"]

import argparse
import asyncio
import io
import json
import lzma
import os
import re
import struct
import sys
import time
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import httpx
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow as pa  # type: ignore[import-untyped]
from app.cli import Client, ClientError, write_table_output
from app.host.capabilities import HostCapabilities, MarketAccess, NetworkAccess
from app.host.jobs import Budget
from app.host.logging import close_host_logging, configure_boot_logging, get_logger
from app.host.network import NetworkUnavailableError, SourceNetwork
from app.host.packages import PreparedContribution
from app.persistence.market import (
    M1_SCHEMA,
    TICK_SCHEMA,
    DefinitionRequest,
    MarketDataset,
)
from app.persistence.resources import ResourceRef
from pydantic import JsonValue

logger = get_logger(__name__)

PLUGIN = {
    "id": "plugin.data_manager.dukascopy",
    "kind": "plugin",
    "version": "1.0.0",
    "compatibility": "1",
    "owner_workspace_id": "workspace.data_manager",
    "slot_id": "data_source.acquisition",
    "contract_version": "1.0.0",
    "requires": [
        {"id": "host.market_data", "version": "1.0.0"},
        {"id": "host.network", "version": "1.0.0"},
        {"id": "host.jobs", "version": "1.0.0"},
        {"id": "host.resources", "version": "1.0.0"},
    ],
    "parameter_schema": {
        "type": "object",
        "properties": {
            "add": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "pattern": "^[A-Z0-9]{2,40}$"},
                    "kind": {"enum": ["ticks", "m1"], "default": "m1"},
                    "instrument": {"type": "string", "maxLength": 80},
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
            "definitions.add": {
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 725,
                        "items": {"type": "string", "pattern": "^[A-Z0-9_]{2,40}$"},
                    },
                    "kind": {"enum": ["m1", "ticks"]},
                    "broker": {"type": "string", "default": "-1"},
                    "postfix": {"type": "string", "pattern": "^[A-Za-z0-9_.-]{0,40}$"},
                    "instruments": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["symbols", "kind"],
                "additionalProperties": False,
            },
            "download.start": {
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "pattern": "^[a-f0-9]{32}$"},
                    "date_from": {
                        "type": "string",
                        "description": "UTC ISO date or date-time; start inclusive",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "UTC ISO date or date-time; end inclusive",
                    },
                    "mode": {
                        "enum": ["standard", "cdn", "cdn-cn"],
                        "default": "standard",
                    },
                    "overwrite": {"type": "boolean", "default": False},
                    "workers": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 16,
                        "default": 4,
                    },
                    "include_weekends": {"type": "boolean", "default": False},
                    "candle_type": {"enum": ["BID", "ASK"], "default": "BID"},
                    "result_representation": {
                        "enum": ["canonical", "provider"],
                        "default": "canonical",
                    },
                },
                "required": ["dataset_id", "date_from", "date_to"],
                "additionalProperties": False,
            },
            "download.results.read": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "pattern": "^[a-f0-9]{32}$"},
                    "offset": {"type": "integer", "minimum": 0, "default": 0},
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 2000,
                        "default": 2000,
                    },
                },
                "required": ["job_id"],
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    },
    "inputs": [
        {"name": "bi5", "type": "bytes", "units": "compressed provider response"}
    ],
    "outputs": [
        {
            "name": "market_rows",
            "type": "Arrow",
            "units": "UTC and base-currency units",
        },
        {
            "name": "provider_rows",
            "type": "immutable Arrow resources",
            "units": "UTC ms and source-rounded individual base-currency volumes",
        },
    ],
}

TICK_RECORD = struct.Struct(">IIIff")
PROVIDER_M1_SCHEMA = pa.schema(
    [
        ("timestamp", pa.timestamp("ms", tz="UTC")),
        *[(name, pa.float64()) for name in ("open", "high", "low", "close")],
        ("volume", pa.float32()),
    ]
)
PROVIDER_TICK_SCHEMA = pa.schema(
    [
        ("timestamp", pa.timestamp("ms", tz="UTC")),
        ("ask", pa.float64()),
        ("bid", pa.float64()),
        ("ask_volume", pa.float32()),
        ("bid_volume", pa.float32()),
    ]
)
RESULT_RESOURCE_ROWS = 100_000
RESULT_PAGE_ROWS = 2000
MAX_RESULT_RESOURCES = 4096
M1_RECORD = struct.Struct(">IIIII f")
DAY_MS = 86_400_000
HOUR_MS = 3_600_000
LZMA_PROPERTIES_BYTES = 5
INT64_MAX = (1 << 63) - 1
MAX_DECOMPRESSED = 128 * 1024 * 1024
FX_SYMBOL = re.compile(r"^[A-Z]{6}$")
FX_CURRENCIES = frozenset(
    {
        "AUD",
        "BRL",
        "CAD",
        "CHF",
        "CNH",
        "CZK",
        "DKK",
        "EUR",
        "GBP",
        "HKD",
        "HUF",
        "INR",
        "JPY",
        "KRW",
        "MXN",
        "NOK",
        "NZD",
        "PLN",
        "RUB",
        "SEK",
        "SGD",
        "TRY",
        "USD",
        "ZAR",
    }
)
HOURS_PER_DAY = 24
FOREX_SYMBOL_LENGTH = 6
DATE_TEXT_LENGTH = 10
MINUTE_TEXT_LENGTH = 16
MAX_NETWORK_WORKERS = 16
MAX_JOB_DAYS_MINUS_ONE = 36525
MAX_DAILY_ROWS = 2_000_000
HTTP_OK = 200
HTTP_MISSING = 404
HTTP_RATE_LIMIT = 429
HTTP_UNAVAILABLE = 503
SATURDAY_WEEKDAY = 5
SUNDAY_WEEKDAY = 6
SUNDAY_START_HOUR = 19
MAX_RATE_LIMIT_RETRIES = 3
INITIAL_RATE_BACKOFF_SECONDS = 0.5

DUKASCOPY_DISCLAIMER_TEXT = (
    "The Dukascopy Trading Tools include different financial information. "
    "Such data are a result of original and unique methods and technology of "
    "information gathering, compilation, analysis and statistical evaluation "
    "developed by Dukascopy Bank SA. Therefore, such data reflect the current "
    "fair value of the respective financial instruments as independently "
    "assessed by Dukascopy Bank SA and NOT the actual values at a given point "
    "in time. If you are looking to obtain actual quotes please contact the "
    "respective entities that provide this information.\n\n"
    "The Dukascopy Trading Tools data and/or any other data available as free "
    "product from Dukascopy Bank's website shall not constitute a forecast of "
    "the market value of any instruments at any future point either, and is not "
    "an investment advice or recommendation in any form.\n\n"
    "Anyone using and/or putting free web products including all or parts of the "
    "information taken from the Dukascopy Trading Tools and/or any other data "
    "available as free product from Dukascopy Bank's website shall put a clear note "
    "to the public that such data are not meant to indicate the actual value at "
    "any given point in time but represent a discretionary assessment by Dukascopy "
    "Bank SA only.\n\n"
    "The market data assessment system is in constant development and is "
    'provided "AS IS", '
    '"AS AVAILABLE", "WITH ALL ITS FAULTS" and is offered without any covenants or any '
    "express, implied or statutory warranties including (without limitation and "
    "qualification) any warranties as to accuracy, functionality, performance, "
    "merchantability, quiet enjoyment, system integration, data accuracy or "
    "fitness for any particular purpose and any warranties arising from trade usage, "
    "course of dealing or course of performance."
)

CDN_DISCLAIMER_TEXT = (
    "In order to provide faster downloads for its clients StrategyQuant offers "
    "pre-packaged Dukascopy data for some of the symbols on its own CDN servers.\n\n"
    "The data available on SQ CDN were created from original Dukascopy data obtained "
    "from Dukascopy website. StrategyQuant does not guarantee that the data prepared "
    "on its CDN servers exactly match Dukascopy data.\n\n"
    'The data are provided "AS IS", "AS AVAILABLE", "WITH ALL ITS FAULTS" and is '
    "offered without any covenants or any express, implied or statutory warranties "
    "including (without limitation and qualification) any warranties as to accuracy, "
    "functionality, performance, merchantability, quiet enjoyment, system integration, "
    "data accuracy or fitness for any particular purpose and any warranties arising "
    "from trade usage, course of dealing or course of performance."
)


KNOWN_SYMBOLS: dict[str, tuple[int, float, str]] = {
    "EURUSD": (5, 100000.0, "Forex"),
    "GBPUSD": (5, 100000.0, "Forex"),
    "USDJPY": (3, 1000.0, "Forex"),
    "USDCHF": (5, 100000.0, "Forex"),
    "AUDUSD": (5, 100000.0, "Forex"),
    "NZDUSD": (5, 100000.0, "Forex"),
    "USDCAD": (5, 75000.0, "Forex"),
    "EURGBP": (5, 132000.0, "Forex"),
    "EURJPY": (3, 900.0, "Forex"),
    "GBPJPY": (3, 900.0, "Forex"),
    "AUDJPY": (3, 900.0, "Forex"),
    "CADJPY": (3, 900.0, "Forex"),
    "CHFJPY": (3, 900.0, "Forex"),
    "NZDJPY": (3, 900.0, "Forex"),
    "EURAUD": (5, 73000.0, "Forex"),
    "EURCAD": (5, 75000.0, "Forex"),
    "EURCHF": (5, 100000.0, "Forex"),
    "EURNZD": (5, 70000.0, "Forex"),
    "GBPAUD": (5, 73000.0, "Forex"),
    "GBPCAD": (5, 75000.0, "Forex"),
    "GBPCHF": (5, 100000.0, "Forex"),
    "GBPNZD": (5, 70000.0, "Forex"),
    "AUDCAD": (5, 75000.0, "Forex"),
    "AUDCHF": (5, 100000.0, "Forex"),
    "AUDNZD": (5, 68000.0, "Forex"),
    "NZDCAD": (5, 75000.0, "Forex"),
    "NZDCHF": (5, 100000.0, "Forex"),
    "CADCHF": (5, 100000.0, "Forex"),
    "XAUUSD": (3, 100.0, "Metals"),
    "XAGUSD": (3, 5000.0, "Metals"),
    "XPTUSD": (3, 100.0, "Metals"),
    "XPDUSD": (3, 100.0, "Metals"),
    "USA500IDXUSD": (3, 100.0, "Indices"),
    "US500": (3, 100.0, "Indices"),
    "USA30IDXUSD": (3, 10.0, "Indices"),
    "US30": (3, 10.0, "Indices"),
    "USATECHIDXUSD": (3, 20.0, "Indices"),
    "USTECH": (3, 20.0, "Indices"),
    "DEUIDXEUR": (3, 25.0, "Indices"),
    "GER40": (3, 25.0, "Indices"),
    "GBRIDXGBP": (3, 10.0, "Indices"),
    "UK100": (3, 10.0, "Indices"),
    "JPNIDXJPY": (3, 100.0, "Indices"),
    "JP225": (3, 100.0, "Indices"),
    "DOLLARIDXUSD": (3, 1000.0, "Indices"),
    "BRENTCMDUSD": (3, 1000.0, "Commodities"),
    "LIGHTCMDUSD": (3, 1000.0, "Commodities"),
    "GASCMDUSD": (4, 10000.0, "Commodities"),
    "COPPERCMDUSD": (4, 25000.0, "Commodities"),
    "BTCUSD": (2, 1.0, "Crypto"),
    "ETHUSD": (2, 1.0, "Crypto"),
    "LTCUSD": (2, 1.0, "Crypto"),
}


SYMBOL_DETAILS: dict[
    str, tuple[int, float, str, str | None, str | None, float | None]
] = {
    "0005HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0027HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0175HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0291HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0386HKHKD": (3, 1.0, "Stocks", "2018-03-01", "2018-03-01", 0.01),
    "0388HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0700HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0857HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0883HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0939HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "0941HKHKD": (3, 1.0, "Stocks", "2018-04-10", "2018-04-10", 0.01),
    "0998HKHKD": (3, 1.0, "Stocks", "2018-02-05", "2018-02-05", 0.01),
    "1093HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "1177HKHKD": (3, 1.0, "Stocks", "2018-05-25", "2018-05-25", 0.01),
    "1288HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "1299HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "1398HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "1810HKHKD": (3, 1.0, "Stocks", "2022-09-29", "2022-09-29", 0.01),
    "1918HKHKD": (3, 1.0, "Stocks", "2018-02-05", "2018-02-05", 0.01),
    "2007HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "2018HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "2318HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "2388HKHKD": (3, 1.0, "Stocks", "2018-03-01", "2018-03-01", 0.01),
    "2628HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "3333HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "3968HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "3988HKHKD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "3M CO": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "A2A SPA": (3, 1.0, "Stocks", "2020-06-29", "2020-06-29", 0.01),
    "A2AITEUR": (3, 1.0, "Stocks", "2020-06-29", "2020-06-29", 0.01),
    "AAC TECHNOLOGIES HOLDINGS INC": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "AALGBGBX": (3, 1.0, "Stocks", "2015-08-25", "2015-08-25", 0.01),
    "AALUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AAPLUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AAUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ABB LTD": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "ABBNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "ABBOTT LABORATORIES": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ABBSESEK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ABCUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ABEESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ABERDEEN ASSET MANAGEMENT PLC": (
        3,
        1.0,
        "Stocks",
        "2016-09-06",
        "2016-09-06",
        0.01,
    ),
    "ABERTIS INFRAESTRUCTURAS SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ABEVUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ABFGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "ABIBEEUR": (3, 1.0, "Stocks", "2016-11-21", "2016-11-21", 0.01),
    "ABTUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ACAFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "ACCOR SA": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "ACERINOX SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ACFREUR": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "ACS ACTIVIDADES DE CONSTRUCCION Y SERVICIOS SA": (
        3,
        1.0,
        "Stocks",
        "2016-11-14",
        "2016-11-14",
        0.01,
    ),
    "ACSESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ACTELION LTD": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "ACTIVISION BLIZZARD INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ACXESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ADBEUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ADECCO SA": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "ADENCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "ADIDAS AG": (3, 1.0, "Stocks", "2015-03-13", "2015-03-13", 0.01),
    "ADMGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "ADMIRAL GROUP PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "ADNGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "ADOBE SYSTEMS INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ADPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ADSDEEUR": (3, 1.0, "Stocks", "2015-03-13", "2015-03-13", 0.01),
    "ADVANCED MICRO DEVICES": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AEGON NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "AENA SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "AENAESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "AEPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AETNA INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "AETUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "AFFREUR": (3, 1.0, "Stocks", "2016-09-27", "2016-09-27", 0.01),
    "AGEAS": (3, 1.0, "Stocks", "2016-11-21", "2016-11-21", 0.01),
    "AGGREKO PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "AGILENT TECHNOLOGIES INC": (3, 1.0, "Stocks", "2017-05-25", "2017-05-25", 0.01),
    "AGKGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "AGLITEUR": (3, 1.0, "Stocks", "2020-06-10", "2020-06-10", 0.01),
    "AGNNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "AGRICULTURAL BANK OF CHINA LTD": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "AGSBEEUR": (3, 1.0, "Stocks", "2016-11-21", "2016-11-21", 0.01),
    "AHNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "AHTGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "AIA GROUP LTD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "AIFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "AIGUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "AIR FRANCE-KLM": (3, 1.0, "Stocks", "2016-09-27", "2016-09-27", 0.01),
    "AIR LIQUIDE SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "AIR PRODUCTS & CHEMICALS INC": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "AIRBUS GROUP SE": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "AIRFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "AKZANLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "AKZO NOBEL NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "ALCOA INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ALEXION PHARMACEUTICALS INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ALFA LAVAL AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "ALFASESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "ALIBABA GROUP HOLDING-SP ADR": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "ALLIANZ SE": (3, 1.0, "Stocks", "2015-04-09", "2015-04-09", 0.01),
    "ALLSTATE CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ALLUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ALOFREUR": (3, 1.0, "Stocks", "2016-09-27", "2016-09-27", 0.01),
    "ALPHABET INC-CL A": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ALPHABET INC-CL C": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ALSTOM SA": (3, 1.0, "Stocks", "2016-09-27", "2016-09-27", 0.01),
    "ALTRIA GROUP INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ALVDEEUR": (3, 1.0, "Stocks", "2015-04-09", "2015-04-09", 0.01),
    "ALXNUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AMADEUS IT HOLDING SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "AMATUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "AMAZONCOM INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AMBEV SA": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AMDUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AMERICAN AIRLINES GROUP INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AMERICAN ELECTRIC POWER": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AMERICAN EXPRESS CO": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AMERICAN INTERNATIONAL GROUP": (
        3,
        1.0,
        "Stocks",
        "2017-05-11",
        "2017-05-11",
        0.01,
    ),
    "AMERICAN TOWER CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AMERIPRISE FINANCIAL INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "AMERISOURCEBERGEN CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "AMGEN INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AMGNUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AMPITEUR": (3, 1.0, "Stocks", "2020-06-29", "2020-06-29", 0.01),
    "AMPLIFON SPA": (3, 1.0, "Stocks", "2020-06-29", "2020-06-29", 0.01),
    "AMPUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "AMSESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "AMTUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AMZNUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ANADARKO PETROLEUM CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ANGLO AMERICAN PLC": (3, 1.0, "Stocks", "2015-08-25", "2015-08-25", 0.01),
    "ANHEUSER-BUSCH INBEV NV": (3, 1.0, "Stocks", "2016-11-21", "2016-11-21", 0.01),
    "ANTHEM INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ANTMUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ANTOFAGASTA PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "ANTOGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "AP MOELLER - MAERSK A/S": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "APACHE CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "APAUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "APCUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "APDUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "APPLE INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "APPLIED MATERIALS": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ARCELORMITTAL": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "ASHTEAD GROUP PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "ASML HOLDING NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "ASMLNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "ASSICURAZIONI GENERALI SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "ASSOCIATED BRITISH FOODS PLC": (
        3,
        1.0,
        "Stocks",
        "2016-09-06",
        "2016-09-06",
        0.01,
    ),
    "ASTRAZENECA PLC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AT&T INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ATCOASESEK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ATLANTIA SPA": (3, 1.0, "Stocks", "2020-06-29", "2020-06-29", 0.01),
    "ATLAS COPCO AB": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ATLITEUR": (3, 1.0, "Stocks", "2020-06-29", "2020-06-29", 0.01),
    "ATLNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "ATVIUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "AUDCAD": (5, 75000.0, "Forex", "2006-01-03", "2007-03-13", 0.0001),
    "AUDCHF": (5, 100000.0, "Forex", "2006-03-01", "2006-03-01", 0.0001),
    "AUDJPY": (3, 900.0, "Forex", "2003-12-01", "2003-12-01", 0.01),
    "AUDNZD": (5, 68000.0, "Forex", "2006-12-12", "2006-12-12", 0.0001),
    "AUDSGD": (5, 73000.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "AUDUSD": (5, 100000.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "AUSIDXAUD": (3, 25.0, "Indices", "2013-02-26", "2013-02-26", 1.0),
    "AUSTRALIA 200 INDEX": (3, 25.0, "Indices", "2013-02-26", "2013-02-26", 1.0),
    "AUSUSD": (3, 1.0, "Stocks", "2017-05-25", "2017-05-25", 0.01),
    "AUTOGRILL SPA": (3, 1.0, "Stocks", "2020-06-10", "2020-06-10", 0.01),
    "AUTOMATIC DATA PROCESSING": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AUTOZONE INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AVALONBAY COMMUNITIES INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AVBUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AVGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "AVGOUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AVIVA PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "AXA SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "AXPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "AZIMUT HOLDING SPA": (3, 1.0, "Stocks", "2020-06-29", "2020-06-29", 0.01),
    "AZMITEUR": (3, 1.0, "Stocks", "2020-06-29", "2020-06-29", 0.01),
    "AZNGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "AZNSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "AZNUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "AZOUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "BABAUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BABCOCK INTERNATIONAL GROUP PLC": (
        3,
        1.0,
        "Stocks",
        "2016-09-06",
        "2016-09-06",
        0.01,
    ),
    "BABGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BACUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BAE SYSTEMS PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BAERCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "BAGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BAIDU INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "BAMIITEUR": (3, 1.0, "Stocks", "2020-10-01", "2020-10-01", 0.01),
    "BANCA MONTE DEI PASCHI DI SIENA SPA": (
        3,
        1.0,
        "Stocks",
        "2020-12-20",
        "2020-12-20",
        0.01,
    ),
    "BANCO BILBAO VIZCAYA ARGENTARIA SA": (
        3,
        1.0,
        "Stocks",
        "2016-11-14",
        "2016-11-14",
        0.01,
    ),
    "BANCO BPM SPA": (3, 1.0, "Stocks", "2020-10-01", "2020-10-01", 0.01),
    "BANCO BRADESCO SA": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BANCO DE SABADELL SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "BANCO POPULAR ESPANOL SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "BANCO SANTANDER SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "BANK OF AMERICA CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BANK OF CHINA LTD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "BANK OF IRELAND PLC": (3, 1.0, "Stocks", "2020-06-10", "2020-06-10", 0.01),
    "BANK OF NEW YORK MELLON CORP": (
        3,
        1.0,
        "Stocks",
        "2017-05-11",
        "2017-05-11",
        0.01,
    ),
    "BARCGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BARCLAYS PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BASDEEUR": (3, 1.0, "Stocks", "2015-04-22", "2015-04-22", 0.01),
    "BASF SE": (3, 1.0, "Stocks", "2015-04-22", "2015-04-22", 0.01),
    "BATSGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BAUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BAYER AG": (3, 1.0, "Stocks", "2015-03-23", "2015-03-20", 0.01),
    "BAYERISCHE MOTOREN WERKE AG": (3, 1.0, "Stocks", "2015-04-08", "2015-04-08", 0.01),
    "BAYNDEEUR": (3, 1.0, "Stocks", "2015-03-23", "2015-03-20", 0.01),
    "BB&T CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BBDUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BBTUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BBVAESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "BBYUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BCITEUR": (3, 1.0, "Stocks", "2020-11-04", "2020-11-04", 0.01),
    "BDXUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BECTON DICKINSON AND CO": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BEIDEEUR": (3, 1.0, "Stocks", "2015-03-20", "2015-03-20", 0.01),
    "BEIERSDORF AG": (3, 1.0, "Stocks", "2015-03-20", "2015-03-20", 0.01),
    "BELGBEEUR": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "BERKSHIRE HATHAWAY INC-CL B": (3, 1.0, "Stocks", "2017-11-06", "2017-11-06", 0.01),
    "BEST BUY CO INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BHP BILLITON PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BIDUUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "BIIBUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BIOGEN INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BIRGIEEUR": (3, 1.0, "Stocks", "2020-06-10", "2020-06-10", 0.01),
    "BKUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BLNDGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BLTGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BMPSITEUR": (3, 1.0, "Stocks", "2020-12-20", "2020-12-20", 0.01),
    "BMWDEEUR": (3, 1.0, "Stocks", "2015-04-08", "2015-04-08", 0.01),
    "BMYUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BNFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "BNP PARIBAS SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "BNPFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "BNZLGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BOC HONG KONG (HOLDINGS) LTD": (
        3,
        1.0,
        "Stocks",
        "2018-03-01",
        "2018-03-01",
        0.01,
    ),
    "BOEING CO": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BOSSDEEUR": (3, 1.0, "Stocks", "2015-04-09", "2015-04-09", 0.01),
    "BOSTON SCIENTIFIC CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BOUYGUES SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "BP PLC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BPEITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "BPER BANCA SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "BPGBGBX": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BPUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BRBYGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "BREITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "BREMBO SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "BRENTCMDUSD": (3, 100.0, "Commodities", "2013-01-01", "2013-01-01", 0.01),
    "BRISTOL-MYERS SQUIBB CO": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BRITISH AMERICAN TOBACCO PLCSTOCKS": (
        3,
        1.0,
        "Stocks",
        "2016-09-06",
        "2016-09-06",
        0.01,
    ),
    "BRITISH LAND CO PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BRKBUSUSD": (3, 1.0, "Stocks", "2017-11-06", "2017-11-06", 0.01),
    "BROADCOM LIMITED": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "BRUNELLO CUCINELLI SPA": (3, 1.0, "Stocks", "2020-11-04", "2020-11-04", 0.01),
    "BSXUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "BT GROUP PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "BTCUSD": (1, 1.0, "Crypto", "2017-05-08", "2017-05-08", 0.01),
    "BTGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "BUNDTREUR": (3, 1.0, "Bond", "2018-05-03", "2018-05-03", 0.01),
    "BUNZL PLC": (3, 1.0, "Stocks", "2016-09-06", "2016-09-06", 0.01),
    "BURBERRY GROUP PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "BUZZI UNICEM SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "BZUITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "CABKESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "CADCHF": (5, 100000.0, "Forex", "2006-01-03", "2006-01-03", 0.0001),
    "CADHKD": (5, 12500.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "CADJPY": (3, 900.0, "Forex", "2004-10-25", "2004-10-25", 0.01),
    "CAFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "CAGUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CAHUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CAIXABANK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "CAP GEMINI SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "CAPFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "CAPITA PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "CAPITAL ONE FINANCIAL CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CARDINAL HEALTH INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CARLBDKDKK": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "CARLSBERG A/S": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "CARNIVAL PLC": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "CARREFOUR SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "CASSITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "CATERPILLLAR INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CATTOLICA ASS COOP A": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "CATUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CBKDEEUR": (3, 1.0, "Stocks", "2015-03-26", "2015-03-26", 0.01),
    "CBS CORP-CLASS B NON VOTING": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CBSUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CCLGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "CENTRICA PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "CENTURYLINK INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CERVED INFORMATION SOLIUTIONS SPA": (
        3,
        1.0,
        "Stocks",
        "2020-12-21",
        "2020-12-21",
        0.01,
    ),
    "CERVITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "CF INDUSTRIES HOLDINGS INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CFUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CHEIDXCHF": (3, 25.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "CHEVRON CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CHFJPY": (3, 900.0, "Forex", "2003-08-04", "2003-08-04", 0.01),
    "CHFPLN": (5, 27000.0, "Forex", "2007-03-15", "2007-03-15", 0.0001),
    "CHFSGD": (5, 73000.0, "Forex", "2007-06-05", "2007-06-05", 0.0001),
    "CHIIDXUSD": (3, 25.0, "Indices", "2017-07-18", "2017-07-19", 1.0),
    "CHINA A50": (3, 25.0, "Indices", "2017-07-18", "2017-07-19", 1.0),
    "CHINA CONSTRUCTION BANK CORP": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "CHINA EVERGRANDE GROUP": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "CHINA LIFE INSURANCE COMPANY LTD": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "CHINA MERCHANTS BANK CO LTD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "CHINA MOBILE LTD": (3, 1.0, "Stocks", "2018-04-10", "2018-04-10", 0.01),
    "CHINA NATIONAL OFFSHORE OIL CORPORATION LTD": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "CHINA RESOURCES BEER HOLDINGS CO LTD": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "CHIPOTLE MEXICAN GRILL INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CIE DE ST-GOBAIN": (3, 1.0, "Stocks", "2016-10-31", "2016-10-31", 0.01),
    "CIGNA CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CISCO SYSTEMS INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CITIC BANK INTERNATIONAL CORP LTD": (
        3,
        1.0,
        "Stocks",
        "2018-02-05",
        "2018-02-05",
        0.01,
    ),
    "CITIGROUP INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CIUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CLARIANT AG": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "CLNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "CLUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CMCSAUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CMGUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CMIUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CNAGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "COCA-COLA COTHE": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "COCOACMDUSD": (3, 100.0, "Commodities", "2017-10-20", "2017-10-23", 0.01),
    "COFFEE ARABICA": (3, 100.0, "Commodities", "2017-12-05", "2017-12-06", 0.01),
    "COFFEECMDUSX": (3, 100.0, "Commodities", "2017-12-05", "2017-12-06", 0.01),
    "COFUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "COLGATE-PALMOLIVE CO": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "COLOBDKDKK": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "COLOPLAST A/S": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "COLUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "COMCAST CORP-CLASS A": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "COMMERZBANK AG": (3, 1.0, "Stocks", "2015-03-26", "2015-03-26", 0.01),
    "COMPASS GROUP PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "CONAGRA FOODS INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CONDEEUR": (3, 1.0, "Stocks", "2015-04-08", "2015-04-08", 0.01),
    "CONOCOPHILLIPS": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CONSTELLATION BRANDS INC-A": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CONSUMER DISCRETIONARY SELECT SECTOR SPDR FUND": (
        3,
        1.0,
        "Stocks",
        "2017-11-15",
        "2017-11-15",
        0.01,
    ),
    "CONSUMER STAPLES SELECT SECTOR SPDR FUND": (
        3,
        1.0,
        "Stocks",
        "2017-11-15",
        "2017-11-15",
        0.01,
    ),
    "CONTINENTAL AG": (3, 1.0, "Stocks", "2015-04-08", "2015-04-08", 0.01),
    "COPPERCMDUSD": (4, 0.01, "Commodities", "2012-03-01", "2012-03-01", 0.0001),
    "COPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CORNING INC": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "COTTON": (3, 100.0, "Commodities", "2017-10-23", "2017-10-23", 0.01),
    "COTTONCMDUSX": (3, 100.0, "Commodities", "2017-10-23", "2017-10-23", 0.01),
    "COUNTRY GARDEN HOLDINGS LTD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "CPGGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "CPIGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "CPRITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "CRDAGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "CREDIT AGRICOLE SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "CREDIT SUISSE GROUP AG": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CREDITO VALTLINESE SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "CRGIEEUR": (3, 1.0, "Stocks", "2020-10-02", "2020-10-02", 0.01),
    "CRH PLC": (3, 1.0, "Stocks", "2016-11-08", "2016-11-08", 0.01),
    "CRHGBGBX": (3, 1.0, "Stocks", "2016-11-08", "2016-11-08", 0.01),
    "CRMUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "CRODA INTERNATIONAL PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "CSCOUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CSFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "CSGNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "CSPC PHARMACEUTICAL GROUP LTD": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "CSUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CTLUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CUMMINS INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "CVALITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "CVS HEALTH CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CVSUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "CVXUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "DAIDEEUR": (3, 1.0, "Stocks", "2015-03-27", "2015-03-27", 0.01),
    "DAIMLER AG": (3, 1.0, "Stocks", "2015-03-27", "2015-03-27", 0.01),
    "DALUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DANAHER CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DANIELI & CO SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "DANITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "DANONE SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "DANSKE BANK A/S": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "DANSKEDKDKK": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "DAVIDE CAMPARI-MILANO SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "DAVITA HEALTHCARE PARTNERS I": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "DB1DEEUR": (3, 1.0, "Stocks", "2015-04-14", "2015-04-14", 0.01),
    "DBKDEEUR": (3, 1.0, "Stocks", "2015-03-25", "2015-03-25", 0.01),
    "DEERE & CO": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "DELTA AIR LINES INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DEUIDXEUR": (3, 27.0, "Indices", "2011-09-19", "2013-09-30", 1.0),
    "DEUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "DEUTSCHE BANK AG": (3, 1.0, "Stocks", "2015-03-25", "2015-03-25", 0.01),
    "DEUTSCHE BOERSE AG": (3, 1.0, "Stocks", "2015-04-14", "2015-04-14", 0.01),
    "DEUTSCHE LUFTHANSA AG": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "DEUTSCHE POST AG": (3, 1.0, "Stocks", "2015-03-31", "2015-03-31", 0.01),
    "DEUTSCHE TELEKOM AG": (3, 1.0, "Stocks", "2015-03-31", "2015-03-31", 0.01),
    "DEVON ENERGY CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DFSUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DGEGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "DGFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "DGUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "DHIUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "DHRUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DIAESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "DIAGEO PLC": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "DIAITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "DIASORIN SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "DIAUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DIESELCMDUSD": (3, 0.01, "Commodities", "2017-10-22", "2017-10-22", 0.01),
    "DISCOVER FINANCIAL SERVICES": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DISTRIBUIDORA INTERNACIONAL DE ALIMENTACION SA": (
        3,
        1.0,
        "Stocks",
        "2016-11-14",
        "2016-11-14",
        0.01,
    ),
    "DISUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "DNB ASA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "DNBNONOK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "DOLLAR GENERAL CORP": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "DOLLARIDXUSD": (3, 25.0, "Indices", "2017-12-01", "2017-12-03", 1.0),
    "DOMINION RESOURCES INCVA": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DPWDEEUR": (3, 1.0, "Stocks", "2015-03-31", "2015-03-31", 0.01),
    "DR HORTON INC": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "DSMNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "DTEDEEUR": (3, 1.0, "Stocks", "2015-03-31", "2015-03-31", 0.01),
    "DUKE ENERGY CORP": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "DUKUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "DUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DVAUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DVNUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "DVYUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EASYJET PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "EAUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "EBAY INC": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "EBAYUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "EBSATEUR": (3, 1.0, "Stocks", "2016-04-11", "2016-04-11", 0.01),
    "EDFFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "EDISON INTERNATIONAL": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "EDP - ENERGIAS DE PORTUGAL SA": (
        3,
        1.0,
        "Stocks",
        "2016-11-14",
        "2016-11-14",
        0.01,
    ),
    "EDPPTEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "EEMUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EFAUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EFXUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "EIFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "EIXUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "ELECCTRONIC ARTS": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "ELECTRICITE DE FRANCE SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "ELECTROLUX AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "ELEESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ELI LILLY & CO": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "ELI1VFIEUR": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "ELISA OYJ": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "ELUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ELUXBSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "EMBUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "EMERSON ELECTRIC CO": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "EMRUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ENAGAS SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ENDESA SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ENEL SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "ENELITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "ENERGY SELECT SECTOR SPDR FUND": (
        3,
        1.0,
        "Stocks",
        "2017-11-15",
        "2017-11-15",
        0.01,
    ),
    "ENFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "ENGESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ENGIE": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "ENGIFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "ENI SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "ENIITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "EOANDEEUR": (3, 1.0, "Stocks", "2015-04-20", "2015-04-20", 0.01),
    "EOG RESOURCES INC": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "EOGUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "EON SE": (3, 1.0, "Stocks", "2015-04-20", "2015-04-20", 0.01),
    "EQT CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "EQTUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "EQUIFAX INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ERG SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "ERGITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "ERICBSESEK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ERSTE GROUP BANK AG": (3, 1.0, "Stocks", "2016-04-11", "2016-04-11", 0.01),
    "ESPIDXEUR": (3, 12.0, "Indices", "2013-02-26", "2011-09-19", 1.0),
    "ESRXUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ESSILOR INTERNATIONAL SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "ESTEE LAUDER COMPANIES-CL A": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "EURAUD": (5, 73000.0, "Forex", "2005-10-08", "2005-10-08", 0.0001),
    "EURCAD": (5, 75000.0, "Forex", "2004-10-25", "2004-10-25", 0.0001),
    "EURCHF": (5, 100000.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "EURCZK": (4, 4500.0, "Forex", "2016-01-03", "2016-01-03", 0.0001),
    "EURDKK": (5, 15600.0, "Forex", "2004-10-25", "2004-10-25", 0.0001),
    "EURGBP": (5, 132000.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "EURHKD": (5, 12500.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "EURHUF": (3, 360.0, "Forex", "2007-03-15", "2007-03-15", 0.0001),
    "EURJPY": (3, 900.0, "Forex", "2003-08-04", "2003-08-04", 0.01),
    "EURNOK": (5, 12200.0, "Forex", "2004-10-25", "2004-10-25", 0.0001),
    "EURNZD": (5, 68000.0, "Forex", "2006-01-03", "2006-01-03", 0.0001),
    "EUROPE 50 INDEX": (3, 12.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "EURPLN": (5, 27000.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "EURRUB": (5, 1573.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "EURSEK": (5, 11200.0, "Forex", "2004-10-28", "2004-10-28", 0.0001),
    "EURSGD": (5, 73000.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "EURTRY": (5, 21000.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "EURUSD": (5, 100000.0, "Forex", "2003-05-05", "2003-05-05", 0.0001),
    "EUSIDXEUR": (3, 12.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "EWHUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EWJUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EWWUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EWZUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EXCUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EXELON CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EXPEDEA INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "EXPERIAN PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "EXPEUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "EXPNGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "EXPRESS SCRIPTS HOLDING": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "EXXON MOBIL CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "EZJGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "EZUUSUSD": (3, 1.0, "Stocks", "2018-02-02", "2018-02-05", 0.01),
    "FACEBOOK INC-A": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "FBKITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "FBUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "FCAITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "FCXUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "FDXUSUSD": (3, 1.0, "Stocks", "2017-02-11", "2017-02-11", 0.01),
    "FEDEX CORP": (3, 1.0, "Stocks", "2017-02-11", "2017-02-11", 0.01),
    "FERESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "FERRAI NV": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "FERROVIAL SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "FEUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "FIAT CHRYSLER AUTO NV": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "FINANCIAL SELECT SECTOR SPDR FUND": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "FINECOBANK BANCA FINECO SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "FIRSTENERGY CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "FMEDEEUR": (3, 1.0, "Stocks", "2015-04-01", "2015-04-01", 0.01),
    "FORD MOTOR CO": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "FPFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "FRAIDXEUR": (3, 12.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "FRANCE 40 INDEX": (3, 12.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "FREDEEUR": (3, 1.0, "Stocks", "2015-04-10", "2015-04-10", 0.01),
    "FREEPORT-MCMORAN INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "FRESENIUS MEDICAL CARE AG & CO KGAA": (
        3,
        1.0,
        "Stocks",
        "2015-04-01",
        "2015-04-01",
        0.01,
    ),
    "FRESENIUS SE & CO KGAA": (3, 1.0, "Stocks", "2015-04-10", "2015-04-10", 0.01),
    "FRESGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "FRESNILLO PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "FRFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "FUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "FXIUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "G4S PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "GALAXY ENTERTAINMENT GROUP LTD": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "GALENICA AG": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "GALNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "GALP ENERGIA SGPS SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "GALPPTEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "GAMESA CORPORACION TECNOLOGICA SA": (
        3,
        1.0,
        "Stocks",
        "2016-11-14",
        "2016-11-14",
        0.01,
    ),
    "GAMESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "GAP INCTHE": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "GAS NATURAL SDG SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "GASCMDUSD": (4, 0.1, "Commodities", "2012-09-02", "2012-09-02", 0.0001),
    "GASESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "GBPAUD": (5, 73000.0, "Forex", "2006-03-22", "2006-03-22", 0.0001),
    "GBPCAD": (5, 75000.0, "Forex", "2006-01-03", "2006-01-03", 0.0001),
    "GBPCHF": (5, 100000.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "GBPJPY": (3, 900.0, "Forex", "2003-08-04", "2003-08-04", 0.01),
    "GBPNZD": (5, 68000.0, "Forex", "2006-01-03", "2006-01-03", 0.0001),
    "GBPUSD": (5, 100000.0, "Forex", "2003-05-05", "2003-05-05", 0.0001),
    "GBRIDXGBP": (3, 13.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "GDXJUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GDXUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GEELY AUTOMOBILE HOLDINGS LTD": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "GEMALTO NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "GENERAL ELECTRIC CO": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GENERAL MILLS INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GENERAL MOTORS CO": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "GERMAN GOVERNMENT BOND": (3, 1.0, "Bond", "2018-05-03", "2018-05-03", 0.01),
    "GERMANY 30 INDEX": (3, 27.0, "Indices", "2011-09-19", "2013-09-30", 1.0),
    "GETIBSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "GETINGE AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "GEUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GFSGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "GILDUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GILEAD SCIENCES INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GISUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "GIVAUDAN SA": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "GIVNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "GKN PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "GKNGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "GLAXOSMITHKLINE PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "GLDUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "GLEFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "GLENCORE PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "GLENGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "GLWUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "GMUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "GOLDMAN SACHS GROUP INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GOOGLUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GOOGUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GPSUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "GSKGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "GSUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "GTONLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "GWWUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "HALLIBURTON CO": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "HALUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "HAMMERSON PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "HCNUSUSD": (3, 1.0, "Stocks", "2018-01-02", "2018-01-02", 0.01),
    "HCP INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "HCPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "HDUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "HEALTH CARE SELECT SECTOR SPDR FUND": (
        3,
        1.0,
        "Stocks",
        "2017-11-15",
        "2017-11-15",
        0.01,
    ),
    "HEIANLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "HEIDEEUR": (3, 1.0, "Stocks", "2015-04-02", "2015-04-02", 0.01),
    "HEIDELBERGCEMENT AG": (3, 1.0, "Stocks", "2015-04-02", "2015-04-02", 0.01),
    "HEINEKEN NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "HEN3DEEUR": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "HENKEL AG & CO KGAA": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "HENNES & MAURITZ AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "HESS CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "HESUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "HIGH GRADE COPPER": (4, 0.01, "Commodities", "2012-03-01", "2012-03-01", 0.0001),
    "HK EXCHANGES & CLEARING LTD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "HKDJPY": (5, 900.0, "Forex", "2007-03-14", "2007-03-14", 0.01),
    "HKGIDXHKD": (3, 5.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "HMBSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "HMSOGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "HOME DEPOT INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "HONEYWELL INTERNATIONAL INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "HONG KONG 40 INDEX": (3, 5.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "HONUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "HP INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "HPQUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "HSBAGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "HSBC HOLDINGS PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "HUGO BOSS AG": (3, 1.0, "Stocks", "2015-04-09", "2015-04-09", 0.01),
    "HUMANA INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "HUMUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IAGGBGBX": (3, 1.0, "Stocks", "2016-11-08", "2016-11-08", 0.01),
    "IBBUSUSD": (3, 1.0, "Stocks", "2017-05-12", "2017-05-15", 0.01),
    "IBEESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "IBERDROLA SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "IBMUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ICEUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IEFUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IFXDEEUR": (3, 1.0, "Stocks", "2015-04-13", "2015-04-13", 0.01),
    "IGITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "IHGGBGBX": (3, 1.0, "Stocks", "2016-11-01", "2016-11-01", 0.01),
    "IJHUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IJRUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ILLINOIS TOOL WORKS": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IMPERIAL BRANDS PLC": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "IMTGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "INDIA 50 INDEX": (3, 25.0, "Indices", "2017-12-04", "2017-12-04", 1.0),
    "INDIDXUSD": (3, 25.0, "Indices", "2017-12-04", "2017-12-04", 1.0),
    "INDITEX SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "INDUSTRIAL AND COMMERCIAL BANK OF CHINA LTD": (
        3,
        1.0,
        "Stocks",
        "2018-01-22",
        "2018-01-22",
        0.01,
    ),
    "INDUSTRIAL SELECT SECTOR SPDR FUND": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "INFINEON TECHNOLOGIES AG": (3, 1.0, "Stocks", "2015-04-13", "2015-04-13", 0.01),
    "INFRASTRUCTURE WIRELESS ITALIANE SPA": (
        3,
        1.0,
        "Stocks",
        "2020-12-21",
        "2020-12-21",
        0.01,
    ),
    "ING GROEP NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "INGANLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "INMARSAT PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "INTCUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "INTEL CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "INTERCONTINENTAL EXCHANGE IN": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "INTERCONTINENTAL HOTELS GROUP PLC": (
        3,
        1.0,
        "Stocks",
        "2016-11-01",
        "2016-11-01",
        0.01,
    ),
    "INTERNATIONAL CONSOLIDATED AIRLINES GROU": (
        3,
        1.0,
        "Stocks",
        "2016-11-08",
        "2016-11-08",
        0.01,
    ),
    "INTERPUBLIC GROUP OF COS INC": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "INTERTEK GROUP PLC": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "INTESA SANPAOLO SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "INTL BUSINESS MACHINES CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "INVEBSESEK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "INVESTOR AB": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "INWITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "IPATH S&P 500 VIX ST FUTURES ETN": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "IPGUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISATGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "ISHARES 20+ YEAR TREASURY BOND ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "ISHARES 7-10 YEAR TREASURY BOND ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "ISHARES CHINA LARGE-CAP ETF": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ISHARES CORE S&P MID-CAP ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "ISHARES CORE S&P SMALL-CAP ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "ISHARES JP MORGAN USD EMERGING MARKETS BOND ETF": (
        3,
        1.0,
        "Stocks",
        "2017-05-11",
        "2017-05-11",
        0.01,
    ),
    "ISHARES MSCI BRAZIL CAPPED": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES MSCI EAFE ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES MSCI EMERGING MARKETS ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "ISHARES MSCI EMU ETF": (3, 1.0, "Stocks", "2018-02-02", "2018-02-05", 0.01),
    "ISHARES MSCI HONG KONG ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES MSCI JAPAN ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES MSCI MEXICO CAPPED": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES NASDAQ BIOTECHNOLOGY ETF": (
        3,
        1.0,
        "Stocks",
        "2017-05-12",
        "2017-05-15",
        0.01,
    ),
    "ISHARES RUSSELL 1000 GROWTH ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "ISHARES RUSSELL 1000 VALUE ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "ISHARES RUSSELL 2000 ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES S&P 500 GROWTH ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES S&P 500 VALUE ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES SELECT DIVIDEND ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES SILVER TRUST ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISHARES US REAL ESTATE ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ISPITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "ITALGAS SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "ITAU UNIBANCO HOLDING SA": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ITRKGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "ITUBUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ITV PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "ITVGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "ITWUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "ITXESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "IVEUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IVWUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IWDUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IWFUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IWMUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "IYRUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "J SAINSBURY PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "JAPAN 225": (3, 10.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "JCIUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "JM SMUCKER COMPANY": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "JNJUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "JNKUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "JOHNSON & JOHNSON": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "JOHNSON CONTROLS INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "JPMORGAN CHASE & CO": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "JPMUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "JPNIDXJPY": (3, 10.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "JULIUS BAER GROUP LTD": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "JUVEITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "JUVENTUS FOOTBAL CLUB SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "JWNUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "K+S AG": (3, 1.0, "Stocks", "2015-04-15", "2015-04-15", 0.01),
    "KBC GROEP NV": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "KBCBEEUR": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "KELLOGG CO": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "KERFREUR": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "KERING": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "KERRY GROUP PLC": (3, 1.0, "Stocks", "2020-06-25", "2020-06-25", 0.01),
    "KEYCORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KEYUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KGFGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "KIMBERLY-CLARK CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KINDER MORGAN INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KINGFISHER PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "KINGSPAN GROUP PLC": (3, 1.0, "Stocks", "2020-06-25", "2020-06-25", 0.01),
    "KLEPIERRE": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "KMBUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KMIUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KNINCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "KOHLS CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KONINKLIJKE AHOLD DELHAIZE NV": (
        3,
        1.0,
        "Stocks",
        "2016-11-15",
        "2016-11-15",
        0.01,
    ),
    "KONINKLIJKE DSM NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "KONINKLIJKE KPN NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "KONINKLIJKE PHILIPS NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "KONINKLIJKE VOPAK NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "KOUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "KPNNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "KROGER CO": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KRUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KRXIEEUR": (3, 1.0, "Stocks", "2020-06-25", "2020-06-25", 0.01),
    "KRZIEEUR": (3, 1.0, "Stocks", "2020-06-25", "2020-06-25", 0.01),
    "KSSUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "KUEHNE + NAGEL INTERNATIONAL AG": (
        3,
        1.0,
        "Stocks",
        "2015-06-16",
        "2015-06-16",
        0.01,
    ),
    "KUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "L'OREAL SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "LAFARGE HOLCIM LTD": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "LAND SECURITIES GROUP PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "LANDGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "LANXESS AG": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "LAS VEGAS SANDS CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "LDOITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "LEGAL & GENERAL GROUP PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "LEGRAND SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "LENNAR CORP-A": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "LENUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "LEONARDO SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "LGENGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "LHADEEUR": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "LHNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "LIFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "LIGHTCMDUSD": (3, 100.0, "Commodities", "2013-01-01", "2013-01-01", 0.01),
    "LINDE AG": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "LINDEEUR": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "LLOYDS BANKING GROUP PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "LLOYGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "LLYUSUSD": (3, 1.0, "Stocks", "2017-11-05", "2017-11-05", 0.01),
    "LMTUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "LOCKHEED MARTIN CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "LOEWS CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "LONDON STOCK EXCHANGE GROUP PLC": (
        3,
        1.0,
        "Stocks",
        "2016-07-06",
        "2016-07-06",
        0.01,
    ),
    "LONNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "LONZA GROUP AG": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "LOW SUPLHUR GASOIL": (3, 0.01, "Commodities", "2017-10-22", "2017-10-22", 0.01),
    "LOWE'S COS INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "LOWUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "LRFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "LSEGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "LUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "LUVUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "LVMH MOET HENNESSY LOUIS VUITTON SA": (
        3,
        1.0,
        "Stocks",
        "2016-08-05",
        "2016-08-05",
        0.01,
    ),
    "LVSUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "LXSDEEUR": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "MACY'S INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MAERSKBDKDKK": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "MAPESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "MAPFRE SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "MARATHON OIL CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MARATHON PETROLEUM CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MARINE HARVEST ASA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "MARKS & SPENCER GROUP PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "MASTERCARD INC-CLASS A": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "MAUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "MBITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "MCDONALD'S CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MCDUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MCFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "MCKESSON CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MCKUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MEDIASET SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "MEDIOBANCA SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "MERCK & CO INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MERCK KGAA": (3, 1.0, "Stocks", "2015-03-24", "2015-03-24", 0.01),
    "METLIFE INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "METUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MGM RESORTS INTERNATIONAL": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MGMUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MHGNONOK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "MICROSOFT CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "MKSGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "MMMUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "MNDIGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "MOLSON COORS BREWING CO -B": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MONCITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "MONCLER SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "MONDI PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "MONSANTO CO": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MONUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MORGAN STANLEY": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MOUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MPCUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MRKDEEUR": (3, 1.0, "Stocks", "2015-03-24", "2015-03-24", 0.01),
    "MRKUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MROUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MRWGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "MSFTUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "MSITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "MSUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MTNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "MUENCHENER RUECKVERSICHERUNGS AG": (
        3,
        1.0,
        "Stocks",
        "2015-04-21",
        "2015-04-21",
        0.01,
    ),
    "MUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "MUV2DEEUR": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "NATIONAL GRID PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "NATURAL GAS": (4, 0.1, "Commodities", "2012-09-02", "2012-09-02", 0.0001),
    "NBLUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "NDASESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "NEEUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NEMUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NES1VFIEUR": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "NESNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "NESTE OYJ": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "NESTLE SA": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "NETFLIX INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "NETHERLANDS 25 INDEX": (3, 25.0, "Indices", "2013-02-26", "2013-05-21", 1.0),
    "NEWELL BRANDS INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "NEWMONT MINING CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NEXT PLC": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "NEXTERA ENERGY INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NFLXUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "NGGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "NHYNONOK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "NIKE INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "NKEUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "NLDIDXEUR": (3, 25.0, "Indices", "2013-02-26", "2013-05-21", 1.0),
    "NOBLE ENERGY INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "NOCUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NOKIAN RENKAAT OYJ": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "NORDEA BANK AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "NORDSTROM INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NORFOLK SOUTHERN CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NORSK HYDRO ASA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "NORTHROP GRUMMAN CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NOVARTIS AG": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "NOVNCHCHF": (3, 1.0, "Stocks", "2015-06-16", "2015-06-16", 0.01),
    "NOVO NORDISK A/S": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "NOVOBDKDKK": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "NOVOZYMES A/S": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "NRE1VFIEUR": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "NRG ENERGY INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NRGUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NSCUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "NVDAUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "NVIDIA CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "NWLUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "NXTGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "NZDCAD": (5, 75000.0, "Forex", "2006-01-03", "2006-01-03", 0.0001),
    "NZDCHF": (5, 100000.0, "Forex", "2006-01-03", "2006-01-03", 0.0001),
    "NZDJPY": (3, 900.0, "Forex", "2006-01-03", "2006-01-03", 0.01),
    "NZDUSD": (5, 100000.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "NZYMBDKDKK": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "O'REILLY AUTOMOTIVE INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "OCCIDENTAL PETROLEUM CORP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "OJUICECMDUSX": (3, 100.0, "Commodities", "2017-10-23", "2017-10-23", 0.01),
    "OKEUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "OLD MUTUAL PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "OMCUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "OMLGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "OMNICOM GROUP": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ONEOK INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "ORACLE CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ORAFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "ORANGE JUICE": (3, 100.0, "Commodities", "2017-10-23", "2017-10-23", 0.01),
    "ORANGE SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "ORCLUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ORFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "ORKLA ASA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ORKNONOK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "ORLYUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "OTE1VFIEUR": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "OUT1VFIEUR": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "OUTOKUMPU OYJ": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "OUTOTEC OYJ": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "OXYUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "P G & E CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PAH3DEEUR": (3, 1.0, "Stocks", "2015-04-21", "2015-04-21", 0.01),
    "PALADIUM": (3, 0.1, "Commodities", "2021-07-04", "2021-07-04", 0.001),
    "PANDORA A/S": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "PARKER HANNIFIN CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PAYPAL HOLDINGS INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PBRUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PCGUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PCLNUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PEARSON PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "PEPSICO INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PEPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PERNOD-RICARD SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "PERSIMMON PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "PETROCHINA CO LTD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "PETROFAC LTD": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "PETROLEO BRASILEIRO SA": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PEUGEOT SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "PFCGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "PFEUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PFIZER INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PGRUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PGUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PHIANLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "PHILIP MORRIS INTERNATIONAL": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PHILLIPS 66": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PHUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PIAGGIO & C. SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "PIAITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "PING AN INSURANCE LTD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "PIONEER NATURAL RESOURCES CO": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "PLATINUM": (3, 0.1, "Commodities", "2021-11-01", "2021-11-01", 0.001),
    "PLNIDXPLN": (3, 25.0, "Indices", "2017-12-04", "2017-12-04", 1.0),
    "PMUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PNC FINANCIAL SERVICES GROUP": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "PNCUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PNDORADKDKK": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "POLAND 20 INDEX": (3, 25.0, "Indices", "2017-12-04", "2017-12-04", 1.0),
    "POPESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "PORSCHE AUTOMOBIL HOLDING SE": (
        3,
        1.0,
        "Stocks",
        "2015-04-21",
        "2015-04-21",
        0.01,
    ),
    "POWERSHARES QQQ ETF": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PPG INDUSTRIES INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PPGUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PRAXAIR INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PRICELINE GROUP INCTHE": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PROCTER & GAMBLE COTHE": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "PROGRESSIVE CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PROSIEBENSAT1 MEDIA AG": (3, 1.0, "Stocks", "2015-04-20", "2015-04-20", 0.01),
    "PROXIMUS": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "PRUDENTIAL FINANCIAL INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PRUDENTIAL PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "PRUGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "PRUUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PRYITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "PRYSMIAN SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "PSAUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PSMDEEUR": (3, 1.0, "Stocks", "2015-04-20", "2015-04-20", 0.01),
    "PSNGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "PSONGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "PSXUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PUBFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "PUBLIC STORAGE": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PUBLICIS GROUPE SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "PXDUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PXUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "PYPLUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "QQQUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "RACEITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "RAIFFEISEN BANK INTERNATIONAL AG": (
        3,
        1.0,
        "Stocks",
        "2016-04-02",
        "2016-04-02",
        0.01,
    ),
    "RANDGOLD RESOURCES LTD": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "RANDNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "RANDSTAD HOLDING NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "RANGE RESOURCES CORP": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "RAYTHEON COMPANY": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "RBGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "RBIATEUR": (3, 1.0, "Stocks", "2016-04-02", "2016-04-02", 0.01),
    "RBSGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "RDSANLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "RDSBGBGBX": (3, 1.0, "Stocks", "2016-11-01", "2016-11-01", 0.01),
    "RECITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "RECKITT BENCKISER GROUP PLC": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "RECORDATI INDUSTRIA CHIMICA E FARMA SPA": (
        3,
        1.0,
        "Stocks",
        "2020-12-21",
        "2020-12-21",
        0.01,
    ),
    "RED ELECTRICA CORP SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "RED HAT INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "REEESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "REGIONS FINANCIAL CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "RELGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "RELX NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "RELX PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "RENAULT SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "RENNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "REPESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "REPSOL SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "RFUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "RHTUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "RIFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "RIO TINTO PLC": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "RIOGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "RMGGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "RNOFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "ROCHE HOLDING AG": (3, 1.0, "Stocks", "2015-07-03", "2015-07-03", 0.01),
    "ROCKWELL COLLINS INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "ROGCHCHF": (3, 1.0, "Stocks", "2015-07-03", "2015-07-03", 0.01),
    "ROLLS-ROYCE HOLDINGS PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "ROYAL BANK OF SCOTLAND GROUP PLC": (
        3,
        1.0,
        "Stocks",
        "2016-07-08",
        "2016-07-08",
        0.01,
    ),
    "ROYAL DUTCH SHELL PLC": (3, 1.0, "Stocks", "2016-11-01", "2016-11-01", 0.01),
    "ROYAL MAIL PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "RRCUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "RRGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "RRSGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "RSA INSURANCE GROUP PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "RSAGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "RTNUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "RWE AG": (3, 1.0, "Stocks", "2015-04-16", "2015-04-16", 0.01),
    "RWEDEEUR": (3, 1.0, "Stocks", "2015-04-16", "2015-04-16", 0.01),
    "SABESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "SAFFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "SAFRAN SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "SAGE GROUP PLCTHE": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SAIPEM SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "SALESFORCECOM INC": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "SALVAT FERRAGAMO SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "SANDSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SANDVIK AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SANESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "SANFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "SANOFI": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "SAP AG": (3, 1.0, "Stocks", "2015-04-16", "2015-04-16", 0.01),
    "SAPDEEUR": (3, 1.0, "Stocks", "2015-04-16", "2015-04-16", 0.01),
    "SARAS SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "SBRYGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "SCABSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SCHNEIDER ELECTRIC SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "SCHWAB (CHARLES) CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SCHWUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SCMNCHCHF": (3, 1.0, "Stocks", "2015-07-03", "2015-07-03", 0.01),
    "SDFDEEUR": (3, 1.0, "Stocks", "2015-04-15", "2015-04-15", 0.01),
    "SEBASESEK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "SECUBSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SECURITAS AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SEVERN TRENT PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SFERITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "SGDIDXSGD": (3, 25.0, "Indices", "2017-12-01", "2017-12-04", 1.0),
    "SGDJPY": (3, 900.0, "Forex", "2007-03-14", "2007-03-14", 0.01),
    "SGEGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SGOFREUR": (3, 1.0, "Stocks", "2016-10-31", "2016-10-31", 0.01),
    "SGS SA": (3, 1.0, "Stocks", "2015-08-06", "2015-08-06", 0.01),
    "SGSNCHCHF": (3, 1.0, "Stocks", "2015-08-06", "2015-08-06", 0.01),
    "SHERWIN-WILLIAMS COMPANY": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "SHIRE PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SHPGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SHWUSUSD": (3, 1.0, "Stocks", "2017-05-11", "2017-05-11", 0.01),
    "SIEDEEUR": (3, 1.0, "Stocks", "2015-04-20", "2015-04-20", 0.01),
    "SIEMENS AG": (3, 1.0, "Stocks", "2015-04-20", "2015-04-20", 0.01),
    "SIKA AG": (3, 1.0, "Stocks", "2015-08-06", "2015-08-06", 0.01),
    "SIKCHCHF": (3, 1.0, "Stocks", "2015-08-06", "2015-08-06", 0.01),
    "SIMON PROPERTY GROUP INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SINGAPORE BLUE CHIP INDEX": (3, 25.0, "Indices", "2017-12-01", "2017-12-04", 1.0),
    "SINO BIOPHARMECEUTICAL LTD": (3, 1.0, "Stocks", "2018-05-25", "2018-05-25", 0.01),
    "SINOPEC CORP": (3, 1.0, "Stocks", "2018-03-01", "2018-03-01", 0.01),
    "SJMUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "SKABSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SKANDINAVISKA ENSKILDA BANKEN AB": (
        3,
        1.0,
        "Stocks",
        "2016-11-14",
        "2016-11-14",
        0.01,
    ),
    "SKANSKA AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SKF AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SKFBSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SKY PLC": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "SKYGBGBX": (3, 1.0, "Stocks", "2016-07-07", "2016-07-07", 0.01),
    "SLGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SLHNCHCHF": (3, 1.0, "Stocks", "2015-08-06", "2015-08-06", 0.01),
    "SLVUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "SMINGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SMITH & NEPHEW PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SMITHS GROUP PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SNAM SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "SNAP INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SNAPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SNGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SOCIETE GENERALE SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "SOLBBEEUR": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "SOLVAY SA": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "SONOVA HOLDING AG": (3, 1.0, "Stocks", "2015-08-07", "2015-08-07", 0.01),
    "SOONCHCHF": (3, 1.0, "Stocks", "2015-08-07", "2015-08-07", 0.01),
    "SOUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SOUTHERN COTHE": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SOUTHWEST AIRLINES CO": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SOYBEAN": (3, 100.0, "Commodities", "2017-12-03", "2017-12-03", 0.01),
    "SOYBEANCMDUSX": (3, 100.0, "Commodities", "2017-12-03", "2017-12-03", 0.01),
    "SPAIN 35 INDEX": (3, 12.0, "Indices", "2013-02-26", "2011-09-19", 1.0),
    "SPDR BARCLAYS CAPITAL HIGH YIELD BOND ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "SPDR DOW JONES® INDUSTRIAL AVERAGE ETF": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "SPDR GOLD SHARES ETF": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SPDR S&P 500 ETF": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SPDR S&P OIL & GAS EXPLOR & PRODTN ETF": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "SPGUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SPMITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "SPYUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SRENCHCHF": (3, 1.0, "Stocks", "2015-08-07", "2015-08-07", 0.01),
    "SRGITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "SRSITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "SSE PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SSEGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "STANDARD CHARTERED PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "STANDARD LIFE PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "STANGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "STANLEY BLACK & DECKER INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "STATE STREET CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "STATOIL ASA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "STERVFIEUR": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "STIUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "STLNONOK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "STMICROELECTRONICS SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "STMITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "STORA ENSO OYJ": (3, 1.0, "Stocks", "2016-03-11", "2016-03-11", 0.01),
    "STRYKER CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "STTUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "STZUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SUFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "SUGAR WHITE": (3, 100.0, "Commodities", "2017-10-04", "2017-10-04", 0.01),
    "SUGARCMDUSD": (3, 100.0, "Commodities", "2017-10-04", "2017-10-04", 0.01),
    "SUNAC CHINA HOLDINGS LTD": (3, 1.0, "Stocks", "2018-02-05", "2018-02-05", 0.01),
    "SUNTRUST BANKS INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SVENSKA CELLULOSA AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SVTGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "SWATCH GROUP AGTHE": (3, 1.0, "Stocks", "2015-08-07", "2015-08-07", 0.01),
    "SWEDASESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SWEDBANK AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SWEDISH MATCH AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SWISS LIFE HOLDING AG": (3, 1.0, "Stocks", "2015-08-06", "2015-08-06", 0.01),
    "SWISS RE AG": (3, 1.0, "Stocks", "2015-08-07", "2015-08-07", 0.01),
    "SWISSCOM AG": (3, 1.0, "Stocks", "2015-07-03", "2015-07-03", 0.01),
    "SWITZERLAND 20 INDEX": (3, 25.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "SWKUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SWMASESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "SYKUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SYNGENTA AG": (3, 1.0, "Stocks", "2015-08-06", "2015-08-06", 0.01),
    "SYNNCHCHF": (3, 1.0, "Stocks", "2015-08-06", "2015-08-06", 0.01),
    "SYSCO CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "SYYUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TAIWAN SEMICONDUCTOR MANUFACTURING COMPANY LIMITED": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "TAPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TARGET CORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TATE & LYLE PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "TATEGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "TECHNOLOGY SELECT SECTOR SPDR FUND": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "TEFESEUR": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "TEL2BSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "TELE2 AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "TELECOM ITALIA SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TELEFONAKTIEBOLAGET LM ERICSSON": (
        3,
        1.0,
        "Stocks",
        "2016-11-14",
        "2016-11-14",
        0.01,
    ),
    "TELEFONICA SA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "TELENOR ASA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "TELIA COMPANY AB": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "TELNONOK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "TENARIS SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TENCENT HOLDINGS LTD": (3, 1.0, "Stocks", "2018-01-22", "2018-01-22", 0.01),
    "TENITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TERNA SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TESCO PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "TESLA MOTORS INC": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "TEVA PHARMACEUTICAL-SP ADR": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TEVAUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TGTUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "THERMO FISHER SCIENTIFIC INC": (
        3,
        1.0,
        "Stocks",
        "2017-11-02",
        "2017-11-02",
        0.01,
    ),
    "THYSSENKRUPP AG": (3, 1.0, "Stocks", "2015-04-14", "2015-04-14", 0.01),
    "TIFFANY & CO": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TIFUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TIME WARNER INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TISCALI SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TISITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TITITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TJX COMPANIES INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TJXUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TKADEEUR": (3, 1.0, "Stocks", "2015-04-14", "2015-04-14", 0.01),
    "TLS1VFIEUR": (3, 1.0, "Stocks", "2016-09-11", "2016-09-11", 0.01),
    "TLSNSESEK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "TLTUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "TLWGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "TMOUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TODITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TODS SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TOTAL SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "TPKGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "TRAVELERS COS INCTHE": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TRAVIS PERKINS PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "TRNITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "TRVUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TRYJPY": (3, 900.0, "Forex", "2010-05-09", "2010-05-09", 0.01),
    "TSCOGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "TSLAUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "TSMUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TSNUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TUI AG": (3, 1.0, "Stocks", "2015-04-15", "2015-04-15", 0.01),
    "TUI1DEEUR": (3, 1.0, "Stocks", "2015-04-15", "2015-04-15", 0.01),
    "TULLOW OIL PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "TUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "TWITTER INC": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TWTRUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TWXUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "TYSON FOODS INC-CL A": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "UBS GROUP AG": (3, 1.0, "Stocks", "2015-06-15", "2015-06-15", 0.01),
    "UBSGCHCHF": (3, 1.0, "Stocks", "2015-06-15", "2015-06-15", 0.01),
    "UCB SA": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "UCBBEEUR": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "UCGITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "UGFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "UHRCHCHF": (3, 1.0, "Stocks", "2015-08-07", "2015-08-07", 0.01),
    "UK 100 INDEX": (3, 13.0, "Indices", "2011-09-19", "2011-09-19", 1.0),
    "UK GOVERNMENT BOND": (3, 1.0, "Bond", "2017-12-28", "2017-12-28", 0.01),
    "UKGILTTRGBP": (3, 1.0, "Bond", "2017-12-28", "2017-12-28", 0.01),
    "ULNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "ULVRGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "UMIBEEUR": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "UMICORESA": (3, 1.0, "Stocks", "2016-07-11", "2016-07-11", 0.01),
    "UNANLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "UNHUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "UNIBAIL-RODAMCO SE": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "UNICREDIT SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "UNILEVER NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "UNILEVER PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "UNION PACIFIC CORP": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "UNIPOLSAI ASSICURAZIONI SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "UNITED PARCEL SERVICE-CL B": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "UNITED STATES OILSTOCKS": (3, 1.0, "Stocks", "2017-01-26", "2017-11-15", 0.01),
    "UNITED STATES STEEL CORP": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "UNITED TECHNOLOGIES CORP": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "UNITED UTILITIES GROUP PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "UNITEDHEALTH GROUP INC": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "UNPUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "UPSUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "US BANCORP": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "US BRENT CRUDE OIL": (3, 100.0, "Commodities", "2013-01-01", "2013-01-01", 0.01),
    "US COCOA": (3, 100.0, "Commodities", "2017-10-20", "2017-10-23", 0.01),
    "US DOLLAR INDEX": (3, 25.0, "Indices", "2017-12-01", "2017-12-03", 1.0),
    "US GOVERNMENT BOND": (3, 1.0, "Bond", "2018-12-18", "2018-01-05", 0.01),
    "US SMALL CAP 2000 INDEX": (3, 25.0, "Indices", "2018-08-08", "2019-03-20", 1.0),
    "USA 100 TECHNICAL INDEX": (3, 20.0, "Indices", "2011-09-19", "2011-09-30", 1.0),
    "USA 30 INDEX": (3, 5.0, "Indices", "2011-09-19", "2013-09-30", 1.0),
    "USA 500 INDEX": (3, 50.0, "Indices", "2011-09-19", "2011-09-30", 1.0),
    "USA30IDXUSD": (3, 5.0, "Indices", "2011-09-19", "2013-09-30", 1.0),
    "USA500IDXUSD": (3, 50.0, "Indices", "2011-09-19", "2011-09-30", 1.0),
    "USATECHIDXUSD": (3, 20.0, "Indices", "2011-09-19", "2011-09-30", 1.0),
    "USBUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "USDCAD": (5, 75000.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "USDCHF": (5, 100000.0, "Forex", "2003-05-05", "2003-05-05", 0.0001),
    "USDCNH": (5, 15000.0, "Forex", "2012-06-27", "2012-06-27", 0.0001),
    "USDCZK": (4, 4518.0, "Forex", "2016-01-03", "2016-01-03", 0.0001),
    "USDDKK": (5, 15600.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "USDHKD": (5, 12500.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "USDHUF": (3, 360.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "USDILS": (5, 27500.0, "Forex", "2016-12-15", "2016-12-15", 0.0001),
    "USDJPY": (3, 1000.0, "Forex", "2003-05-05", "2003-05-05", 0.01),
    "USDMXN": (5, 4920.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "USDNOK": (5, 12000.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "USDPLN": (5, 27000.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "USDRON": (5, 25000.0, "Forex", "2016-12-18", "2016-12-18", 0.0001),
    "USDRUB": (3, 1600.0, "Forex", "2007-03-14", "2007-03-14", 0.01),
    "USDSEK": (5, 11200.0, "Forex", "2003-08-04", "2003-08-04", 0.0001),
    "USDSGD": (5, 73000.0, "Forex", "2004-11-17", "2004-11-17", 0.0001),
    "USDTHB": (5, 3000.0, "Forex", "2017-02-13", "2017-02-13", 0.0001),
    "USDTRY": (5, 21000.0, "Forex", "2007-03-14", "2007-03-14", 0.0001),
    "USDZAR": (5, 7300.0, "Forex", "2002-02-02", "2002-02-02", 0.0001),
    "USITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "USOUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-11-15", 0.01),
    "USSC2000IDXUSD": (3, 25.0, "Indices", "2018-08-08", "2019-03-20", 1.0),
    "USTBONDTRUSD": (3, 1.0, "Bond", "2018-12-18", "2018-01-05", 0.01),
    "UTILITIES SELECT SECTOR SPDR FUND": (
        3,
        1.0,
        "Stocks",
        "2017-11-15",
        "2017-11-15",
        0.01,
    ),
    "UTXUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "UUGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "VALE SA": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "VALEO SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "VALERO ENERGY CORP": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VALEUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "VALLOUREC SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "VANECK VECTORS GOLD MINERS ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "VANECK VECTORS JUNIOR GOLD MINERS ETF": (
        3,
        1.0,
        "Stocks",
        "2017-01-26",
        "2017-01-26",
        0.01,
    ),
    "VANGUARD FTSE DEVELOPED MARKETS ETF": (
        3,
        1.0,
        "Stocks",
        "2017-11-15",
        "2017-11-15",
        0.01,
    ),
    "VANGUARD FTSE EUROPE ETF": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VANGUARD REIT ETF": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VEAUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VELOCITYSHARES DAILY INVERSE VIX SHORT TERM ETN": (
        3,
        1.0,
        "Stocks",
        "2017-11-15",
        "2017-11-15",
        0.01,
    ),
    "VEOLIA ENVIRONNEMENT SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "VERIZON COMMUNICATIONS INC": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VESTAS WIND SYSTEMS A/S": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "VF CORP": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VFCUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VGKUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VIEFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "VINCI SA": (3, 1.0, "Stocks", "2016-09-30", "2016-09-30", 0.01),
    "VISA INC-CLASS A SHARES": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "VIVENDI SA": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "VIVFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "VKFREUR": (3, 1.0, "Stocks", "2016-08-05", "2016-08-05", 0.01),
    "VLOUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VMCUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VNADEEUR": (3, 1.0, "Stocks", "2015-04-14", "2015-04-14", 0.01),
    "VNQUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VODAFONE GROUP PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "VODGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "VOEATEUR": (3, 1.0, "Stocks", "2016-04-11", "2016-04-11", 0.01),
    "VOESTALPINE AG": (3, 1.0, "Stocks", "2016-04-11", "2016-04-11", 0.01),
    "VOLKSWAGEN AG": (3, 1.0, "Stocks", "2015-04-14", "2015-04-14", 0.01),
    "VOLVBSESEK": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "VOLVO AB": (3, 1.0, "Stocks", "2016-11-07", "2016-11-07", 0.01),
    "VONOVIA SE": (3, 1.0, "Stocks", "2015-04-14", "2015-04-14", 0.01),
    "VOW3DEEUR": (3, 1.0, "Stocks", "2015-04-14", "2015-04-14", 0.01),
    "VPKNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "VULCAN MATERIALS CO": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "VUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "VWSDKDKK": (3, 1.0, "Stocks", "2016-08-11", "2016-08-11", 0.01),
    "VXXUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "VZUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "WAL-MART STORES INC": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "WALT DISNEY COTHE": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "WBDITEUR": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "WEBUILD SPA": (3, 1.0, "Stocks", "2020-12-21", "2020-12-21", 0.01),
    "WEIR GROUP PLCTHE": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "WEIRGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "WELLS FARGO & CO": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "WELLTOWER INC": (3, 1.0, "Stocks", "2018-01-02", "2018-01-02", 0.01),
    "WFCUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "WHIRLPOOL CORP": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "WHITBREAD PLC": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "WHRUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "WKLNLEUR": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "WM MORRISON SUPERMARKETS PLC": (
        3,
        1.0,
        "Stocks",
        "2016-07-07",
        "2016-07-07",
        0.01,
    ),
    "WMTUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "WOLSELEY PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "WOLTERS KLUWER NV": (3, 1.0, "Stocks", "2016-11-15", "2016-11-15", 0.01),
    "WOSGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "WPP PLC": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "WPPGBGBX": (3, 1.0, "Stocks", "2016-07-08", "2016-07-08", 0.01),
    "WTBGBGBX": (3, 1.0, "Stocks", "2016-07-06", "2016-07-06", 0.01),
    "WTI LIGHT CRUDE OIL": (3, 100.0, "Commodities", "2013-01-01", "2013-01-01", 0.01),
    "WW GRAINGER INC": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "XAGUSD": (3, 5000.0, "Forex", "2003-08-08", "2003-08-08", 0.01),
    "XAUUSD": (3, 100.0, "Forex", "2003-05-05", "2003-05-05", 0.01),
    "XIAOMI CORP": (3, 1.0, "Stocks", "2022-09-29", "2022-09-29", 0.01),
    "XIVUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "XLEUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "XLFUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "XLIUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "XLKUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "XLPUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "XLUUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "XLVUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "XLYUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "XOMUSUSD": (3, 1.0, "Stocks", "2017-01-26", "2017-01-26", 0.01),
    "XOPUSUSD": (3, 1.0, "Stocks", "2017-11-02", "2017-11-02", 0.01),
    "XPDCMDUSD": (3, 0.1, "Commodities", "2021-07-04", "2021-07-04", 0.001),
    "XPTCMDUSD": (3, 0.1, "Commodities", "2021-11-01", "2021-11-01", 0.001),
    "XUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "YARA INTERNATIONAL ASA": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "YARNONOK": (3, 1.0, "Stocks", "2016-11-14", "2016-11-14", 0.01),
    "YUM! BRANDS INC": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "YUMUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "ZARJPY": (3, 900.0, "Forex", "2007-06-04", "2007-06-04", 0.01),
    "ZBHUSUSD": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "ZIMMER BIOMET HOLDINGS INC": (3, 1.0, "Stocks", "2017-11-15", "2017-11-15", 0.01),
    "ZURICH INSURANCE GROUP AG": (3, 1.0, "Stocks", "2015-08-07", "2015-08-07", 0.01),
    "ZURNCHCHF": (3, 1.0, "Stocks", "2015-08-07", "2015-08-07", 0.01),
}


@dataclass(frozen=True)
class SymbolInfo:
    """Immutable source catalog entry with price units and inception dates."""

    decimals: int
    point_size: float
    category: str
    m1_start: date | None = None
    tick_start: date | None = None
    pip_size: float | None = None

    def __iter__(self) -> Iterator[int | float | str]:
        """Preserve source tuple-unpacking compatibility."""
        return iter((self.decimals, self.point_size, self.category))


def _get_symbol_info(symbol: str) -> SymbolInfo:  # noqa: PLR0911 -- source fallback cases.
    """Describe a normalized source instrument without ambient catalog reads."""
    clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
    logger.debug("Describing Dukascopy instrument: %s", clean)
    entry = SYMBOL_DETAILS.get(clean)
    if entry:
        decimals, point, category, m1, ticks, pip = entry
        return SymbolInfo(
            decimals,
            point,
            category,
            date.fromisoformat(m1) if m1 else None,
            date.fromisoformat(ticks) if ticks else None,
            pip,
        )
    if clean in KNOWN_SYMBOLS:
        return SymbolInfo(*KNOWN_SYMBOLS[clean])
    decimals = 5
    if clean.endswith("JPY"):
        return SymbolInfo(3, 1000.0, "Forex/JPY")
    if clean.startswith(("XAU", "GOLD")):
        return SymbolInfo(3, 100.0, "Metals")
    if clean.startswith(("XAG", "SILVER")):
        return SymbolInfo(3, 5000.0, "Metals")
    if clean.startswith(("BTC", "ETH", "SOL")):
        return SymbolInfo(2, 1.0, "Crypto")
    if any(
        token in clean
        for token in (
            "IDX",
            "500",
            "30",
            "100",
            "40",
            "2000",
            "DOW",
            "NAS",
            "DAX",
            "SPX",
        )
    ):
        return SymbolInfo(3, 100.0, "Indices")
    if any(token in clean for token in ("CMD", "BRENT", "WTI", "OIL", "GAS")):
        return SymbolInfo(3, 1000.0, "Commodities")
    return SymbolInfo(
        decimals, 100000.0, "Forex" if len(clean) == FOREX_SYMBOL_LENGTH else "Standard"
    )


def _symbol_decimals(symbol: str) -> int:
    """Use the owner script's explicit scales and deterministic fallback rules."""
    clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
    if not re.fullmatch(r"[A-Z0-9]{2,40}", clean):
        raise ValueError("Invalid Dukascopy symbol")
    if clean in SYMBOL_DETAILS:
        return SYMBOL_DETAILS[clean][0]
    if clean in KNOWN_SYMBOLS:
        return KNOWN_SYMBOLS[clean][0]
    if clean.endswith("JPY") or clean.startswith(("XAU", "GOLD", "XAG", "SILVER")):
        return 3
    if clean.startswith(("BTC", "ETH", "SOL")):
        return 2
    if any(
        token in clean
        for token in (
            "100",
            "40",
            "2000",
            "DOW",
            "NAS",
            "IDX",
            "500",
            "30",
            "DAX",
            "SPX",
            "CMD",
            "BRENT",
            "WTI",
            "OIL",
            "GAS",
        )
    ):
        return 3
    return 5


def _point_value(symbol: str) -> int:
    """Resolve the owner's raw integer price divisor without an FX-only limit."""
    return int(10 ** _symbol_decimals(symbol))


def _standard_url(symbol: str, day: datetime, kind: str, hour: int = 0) -> str:
    """Build SQX's date-indexed HTTP provider URL for one BI5 object."""
    _point_value(symbol)
    if day.tzinfo is None or day.utcoffset() != timedelta(0):
        raise ValueError("Provider date must be UTC")
    if not 0 <= hour < HOURS_PER_DAY or kind not in ("ticks", "m1"):
        raise ValueError("Invalid BI5 request")
    parent = (
        f"https://datafeed.dukascopy.com/datafeed/{symbol}/"
        f"{day.year:04d}/{day.month - 1:02d}/{day.day:02d}"
    )
    suffix = f"/{hour:02d}h_ticks.bi5" if kind == "ticks" else "/BID_candles_min_1.bi5"
    return parent + suffix


CDN_GLOBAL_BASE = "https://cdn.strategyquantcdn.com/data/dukascopy"
CDN_CN_BASE = "https://cdn005.strategyquantcdn.com/data/dukascopy"


class RateCorrector:
    """Source acquisition dynamic inter-request rate throttling controller.

    Adapts delay using multiplicative backoff (+25%) on rate limits and
    transient errors, and progressive reduction (-25%) after 100 consecutive
    successful requests.
    """

    def __init__(
        self,
        min_delay_seconds: float = 0.001,
        max_delay_seconds: float = 10.0,
        success_threshold: int = 100,
    ) -> None:
        self._min_delay = min_delay_seconds
        self._max_delay = max_delay_seconds
        self._delay = min_delay_seconds
        self._success_threshold = success_threshold
        self._consecutive_successes = 0

    @property
    def delay(self) -> float:
        """Current inter-request delay in seconds."""
        return self._delay

    def record_success(self) -> None:
        """Record one successful response and apply recovery when threshold reached."""
        self._consecutive_successes += 1
        if self._consecutive_successes >= self._success_threshold:
            self._delay = max(self._min_delay, self._delay * 0.75)
            self._consecutive_successes = 0
            logger.info(
                "Dukascopy rate throttle delay reduced to %.3fs after %d successes",
                self._delay,
                self._success_threshold,
            )

    def record_failure(self) -> None:
        """Record rate-limit or transient error and apply multiplicative backoff."""
        self._consecutive_successes = 0
        self._delay = min(self._max_delay, max(self._min_delay, self._delay * 1.25))
        logger.warning(
            "Dukascopy rate throttle backoff triggered; increased delay to %.3fs",
            self._delay,
        )

    async def throttle(self) -> None:
        """Wait for the active inter-request delay duration."""
        if self._delay > 0:
            await asyncio.sleep(self._delay)


def _cdn_base_url(mode: Literal["cdn", "cdn-cn"], kind: str) -> str:
    """Return the base SQ CDN URL for the selected region and data timeframe."""
    root = CDN_CN_BASE if mode == "cdn-cn" else CDN_GLOBAL_BASE
    tf = "m1" if kind == "m1" else "tick"
    return f"{root}/{tf}"


def _cdn_metadata_url(mode: Literal["cdn", "cdn-cn"], kind: str, symbol: str) -> str:
    """Return the SQ CDN metadata descriptor URL for a symbol."""
    _point_value(symbol)
    return f"{_cdn_base_url(mode, kind)}/{symbol}/metadata.dat"


def _cdn_archive_url(
    mode: Literal["cdn", "cdn-cn"], kind: str, symbol: str, period: str
) -> str:
    """Return the SQ CDN archive URL for a given period."""
    _point_value(symbol)
    archive_name = f"{period.replace('-', '_')}.zip"
    return f"{_cdn_base_url(mode, kind)}/{symbol}/{archive_name}"


def _decompress(payload: bytes, record_size: int) -> bytes:
    """Apply the owner's ALONE/header-repair sequence with a bounded output."""
    if len(payload) < LZMA_PROPERTIES_BYTES or len(payload) > 16 * 1024 * 1024:
        raise ValueError("BI5 payload length is invalid")
    repaired = payload[:5] + struct.pack("<Q", 2**64 - 1) + payload[5:]
    for candidate in (payload, repaired):
        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        try:
            raw = decoder.decompress(candidate, max_length=MAX_DECOMPRESSED + 1)
        except lzma.LZMAError:
            continue
        if len(raw) > MAX_DECOMPRESSED:
            raise ValueError("BI5 expansion exceeds limit")
        if decoder.eof and len(raw) % record_size == 0:
            return raw
    raise ValueError("BI5 decompression failed or payload is malformed")


def _decode_ticks(
    payload: bytes, hour: datetime, symbol: str
) -> tuple[tuple[int, int, int, int], ...]:
    """Preserve the script's NumPy price and per-side float32 volume rounding."""
    decimals = _symbol_decimals(symbol)
    raw = _decompress(payload, TICK_RECORD.size)
    dtype = np.dtype(
        [
            ("offset_ms", ">i4"),
            ("ask", ">i4"),
            ("bid", ">i4"),
            ("ask_vol", ">f4"),
            ("bid_vol", ">f4"),
        ]
    )
    arr = np.frombuffer(raw, dtype=dtype)
    factor = 10.0**-decimals
    asks = np.round(np.round(arr["ask"] * factor, decimals) * 1_000_000).astype(
        np.int64
    )
    bids = np.round(np.round(arr["bid"] * factor, decimals) * 1_000_000).astype(
        np.int64
    )
    ask_volume = np.round(arr["ask_vol"] * 1e6, 2)
    bid_volume = np.round(arr["bid_vol"] * 1e6, 2)
    if (
        not np.all(np.isfinite(ask_volume))
        or not np.all(np.isfinite(bid_volume))
        or np.any(ask_volume < 0)
        or np.any(bid_volume < 0)
    ):
        raise ValueError("Invalid provider volume")
    volumes = np.round(ask_volume + bid_volume).astype(np.uint64)
    base_ms = int(hour.timestamp() * 1000)
    logger.info("Decoded Dukascopy ticks: symbol=%s rows=%d", symbol, len(arr))
    return tuple(
        (base_ms + int(record["offset_ms"]), int(ask), int(bid), int(volume))
        for record, ask, bid, volume in zip(arr, asks, bids, volumes, strict=True)
    )


def _decode_m1(
    payload: bytes, day: datetime, symbol: str
) -> tuple[tuple[int, float, float, float, float, int], ...]:
    """Preserve the source script's bid OHLC order and NumPy float32 rounding."""
    decimals = _symbol_decimals(symbol)
    raw = _decompress(payload, M1_RECORD.size)
    dtype = np.dtype(
        [
            ("offset_sec", ">i4"),
            ("open", ">i4"),
            ("close", ">i4"),
            ("low", ">i4"),
            ("high", ">i4"),
            ("vol", ">f4"),
        ]
    )
    arr = np.frombuffer(raw, dtype=dtype)
    prices = [
        np.round(arr[name] * 10.0**-decimals, decimals)
        for name in ("open", "high", "low", "close")
    ]
    volume = np.round(arr["vol"] * 1e6, 2)
    if not np.all(np.isfinite(volume)) or np.any(volume < 0):
        raise ValueError("Invalid provider volume")
    volumes = np.round(volume).astype(np.uint64)
    base_ms = int(day.timestamp() * 1000)
    logger.info("Decoded Dukascopy bars: symbol=%s rows=%d", symbol, len(arr))
    return tuple(
        (
            base_ms + int(record["offset_sec"]) * 1000,
            float(o),
            float(h),
            float(low),
            float(c),
            int(v),
        )
        for record, o, h, low, c, v in zip(arr, *prices, volumes, strict=True)
    )


@dataclass(frozen=True)
class DownloadSpec:
    """Validated finite acquisition request, shared by UI and CLI."""

    dataset_id: str
    first: date
    last: date
    overwrite: bool
    mode: Literal["standard", "cdn", "cdn-cn"]
    workers: int = 4
    include_weekends: bool = False
    start_ms: int = 0
    end_ms: int = 0
    candle_type: str = "BID"
    result_representation: str = "canonical"


def _parse_datetime(value: str | date | datetime, is_end: bool = False) -> datetime:
    """Normalize reference date/minute inputs into explicit UTC boundaries."""
    logger.debug("Normalizing Dukascopy time boundary")
    if isinstance(value, datetime):
        return (
            value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        )
    if isinstance(value, date):
        result = datetime.combine(value, datetime.min.time(), tzinfo=UTC)
        return result + timedelta(days=1, microseconds=-1) if is_end else result
    clean = value.strip()
    result = datetime.fromisoformat(clean)
    if len(clean) == DATE_TEXT_LENGTH and is_end:
        result += timedelta(days=1, microseconds=-1)
    elif len(clean) == MINUTE_TEXT_LENGTH and is_end:
        result = result.replace(second=59, microsecond=999999)
    return result.replace(tzinfo=UTC)


def _spec(payload: JsonValue) -> DownloadSpec:
    if not isinstance(payload, dict):
        raise TypeError("Invalid Dukascopy download request")
    dataset_id = payload.get("dataset_id")
    first_raw = payload.get("date_from")
    last_raw = payload.get("date_to")
    overwrite = payload.get("overwrite", False)
    mode_raw = payload.get("mode", "standard")
    workers = payload.get("workers", 4)
    weekends = payload.get("include_weekends", False)
    candle_type = payload.get("candle_type", "BID")
    representation = payload.get("result_representation", "canonical")
    if representation not in ("canonical", "provider"):
        raise ValueError("Invalid result representation")
    if (
        not isinstance(dataset_id, str)
        or not isinstance(first_raw, str)
        or not isinstance(last_raw, str)
    ):
        raise TypeError("Invalid Dukascopy download request")
    if not isinstance(overwrite, bool) or not isinstance(weekends, bool):
        raise TypeError("Invalid overwrite/weekend policy")
    if type(workers) is not int or not 1 <= workers <= MAX_NETWORK_WORKERS:
        raise ValueError("Choose between 1 and 16 network workers")
    if mode_raw not in ("standard", "cdn", "cdn-cn"):
        raise ValueError("Invalid download mode")
    if candle_type not in ("BID", "ASK"):
        raise ValueError("Invalid candle feed")
    first_time = _parse_datetime(first_raw)
    last_time = _parse_datetime(last_raw, is_end=True)
    if (
        first_time > last_time
        or last_time.date() > datetime.now(UTC).date()
        or (last_time - first_time).days > MAX_JOB_DAYS_MINUS_ONE
    ):
        raise ValueError("Choose a finite UTC range of at most 100 years through today")
    mode: Literal["standard", "cdn", "cdn-cn"] = (
        "standard"
        if mode_raw == "standard"
        else "cdn"
        if mode_raw == "cdn"
        else "cdn-cn"
    )
    return DownloadSpec(
        dataset_id,
        first_time.date(),
        last_time.date(),
        overwrite,
        mode,
        workers,
        weekends,
        int(first_time.timestamp() * 1000),
        int(last_time.timestamp() * 1000),
        str(candle_type),
        str(representation),
    )


def _arrow_rows(rows: list[tuple[Any, ...]], kind: str) -> pa.Table:
    """Build exactly the approved Arrow schema from normalized provider rows."""
    schema = TICK_SCHEMA if kind == "ticks" else M1_SCHEMA
    columns: list[pa.Array] = []
    for index, field in enumerate(schema):
        values = [row[index] for row in rows]
        array = pa.array(values, type=pa.int64() if index == 0 else field.type)
        columns.append(array.cast(field.type) if index == 0 else array)
    return pa.Table.from_arrays(columns, schema=schema)


@dataclass(frozen=True)
class DayFetch:
    """Available rows and precise received/failed/missing source chunks."""

    table: Any
    received_intervals: tuple[tuple[int, int], ...]
    modes: frozenset[str]
    failed_chunks: int = 0
    missing_chunks: int = 0
    provider_table: Any = None


def _provider_table(payload: bytes, stamp: datetime, symbol: str, kind: str) -> Any:
    """Decode raw source columns after canonical validation of the same chunk."""
    names = (
        [
            ("offset_ms", ">i4"),
            ("ask", ">i4"),
            ("bid", ">i4"),
            ("ask_vol", ">f4"),
            ("bid_vol", ">f4"),
        ]
        if kind == "ticks"
        else [
            ("offset_sec", ">i4"),
            ("open", ">i4"),
            ("close", ">i4"),
            ("low", ">i4"),
            ("high", ">i4"),
            ("vol", ">f4"),
        ]
    )
    arr = np.frombuffer(
        _decompress(payload, 20 if kind == "ticks" else 24), dtype=np.dtype(names)
    )
    decimals = _symbol_decimals(symbol)
    offsets = arr["offset_ms" if kind == "ticks" else "offset_sec"].astype(np.int64)
    times = int(stamp.timestamp() * 1000) + offsets * (1 if kind == "ticks" else 1000)
    columns = [pa.array(times).cast(pa.timestamp("ms", tz="UTC"))]
    for name in ("ask", "bid") if kind == "ticks" else ("open", "high", "low", "close"):
        columns.append(pa.array(np.round(arr[name] * 10.0**-decimals, decimals)))  # noqa: PERF401 -- distinct typed columns.
    for name in ("ask_vol", "bid_vol") if kind == "ticks" else ("vol",):
        columns.append(pa.array(np.round(arr[name] * 1e6, 2), type=pa.float32()))  # noqa: PERF401 -- distinct typed columns.
    logger.info("Decoded Dukascopy provider result: kind=%s rows=%d", kind, len(arr))
    return pa.Table.from_arrays(
        columns,
        schema=(PROVIDER_TICK_SCHEMA if kind == "ticks" else PROVIDER_M1_SCHEMA),
    )


async def _direct_payload(
    network: NetworkAccess, url: str, corrector: RateCorrector
) -> tuple[bytes, bool]:
    """Try source HTTPS and HTTP, keeping custody/authority errors fatal."""
    failed = False
    for target in (url, url.replace("https://", "http://", 1)):
        try:
            response = await network.get(target)
            for attempt in range(MAX_RATE_LIMIT_RETRIES):
                if response.status not in (429, 500, 502, 503, 504):
                    break
                corrector.record_failure()
                await asyncio.sleep(
                    max(INITIAL_RATE_BACKOFF_SECONDS * 2**attempt, corrector.delay)
                )
                response = await network.get(target)
        except NetworkUnavailableError:
            failed = True
            logger.warning("Dukascopy transport exhausted: %s", target)
            continue
        if response.status == HTTP_OK and response.body:
            corrector.record_success()
            return response.body, False
        failed = failed or response.status not in (HTTP_OK, HTTP_MISSING)
        logger.info(
            "Dukascopy unavailable chunk: status=%d url=%s", response.status, target
        )
    return b"", failed


async def _fetch_day_result(  # noqa: C901, PLR0915 -- bounded source chunk coordinator.
    network: NetworkAccess,
    dataset: MarketDataset,
    day: date,
    rate_corrector: RateCorrector | None = None,
    *,
    archive: dict[datetime, bytes] | None = None,
    archive_mode: str = "cdn",
    skip_intervals: tuple[tuple[int, int], ...] = (),
    workers: int = 4,
    start_ms: int | None = None,
    end_ms: int | None = None,
    candle_type: str = "BID",
    provider_results: bool = False,
) -> DayFetch:
    """Decode bounded concurrent chunks and retain every successful interval."""
    symbol = dataset.symbol.upper()
    midnight = datetime(day.year, day.month, day.day, tzinfo=UTC)
    corrector = rate_corrector or RateCorrector(min_delay_seconds=0.0)
    rows: list[tuple[Any, ...]] = []
    provider_tables: list[Any] = []
    received: list[tuple[int, int]] = []
    modes: set[str] = set()
    failed = missing = 0

    async def chunk(
        hour: int,
    ) -> tuple[list[tuple[Any, ...]], tuple[int, int] | None, str, int, int]:
        stamp = midnight + timedelta(hours=hour)
        first = int(stamp.timestamp() * 1000)
        last = first + (3_600_000 if dataset.kind == "ticks" else DAY_MS) - 1
        if (start_ms is not None and last < start_ms) or (
            end_ms is not None and first > end_ms
        ):
            return [], None, "", 0, 0
        first = max(first, start_ms) if start_ms is not None else first
        last = min(last, end_ms) if end_ms is not None else last
        if any(left <= first and last <= right for left, right in skip_intervals):
            return [], None, "", 0, 0
        url = _standard_url(symbol, midnight, dataset.kind, hour)
        if dataset.kind == "m1" and candle_type == "ASK":
            url = url.replace("BID_candles", "ASK_candles")
        await corrector.throttle()
        payload = (archive or {}).get(stamp, b"")
        mode = archive_mode if payload else "standard"
        decode_failed = False
        if payload:
            try:
                values = (
                    _decode_ticks(payload, stamp, symbol)
                    if dataset.kind == "ticks"
                    else _decode_m1(payload, midnight, symbol)
                )
            except ValueError:
                decode_failed = True
                payload = b""
                logger.warning("Dukascopy invalid CDN chunk; falling back: %s", url)
        if not payload:
            payload, unavailable = await _direct_payload(network, url, corrector)
            mode = "standard"
            if not payload:
                return (
                    [],
                    None,
                    "",
                    int(unavailable or decode_failed),
                    int(not unavailable and not decode_failed),
                )
            try:
                values = (
                    _decode_ticks(payload, stamp, symbol)
                    if dataset.kind == "ticks"
                    else _decode_m1(payload, midnight, symbol)
                )
            except ValueError:
                logger.warning("Dukascopy malformed chunk skipped: %s", url)
                return [], None, "", 1, 0
        selected = [row for row in values if first <= row[0] <= last]
        if provider_results and selected:
            raw_table = _provider_table(payload, stamp, symbol, dataset.kind)
            times = raw_table.column("timestamp").cast(pa.int64()).to_numpy()
            provider_tables.append(
                raw_table.filter(pa.array((times >= first) & (times <= last)))
            )
        return selected, (first, last) if selected else None, mode, 0, int(not selected)

    hours = list(range(HOURS_PER_DAY)) if dataset.kind == "ticks" else [0]
    for offset in range(0, len(hours), workers):
        async with asyncio.TaskGroup() as group:
            tasks = [
                group.create_task(chunk(hour))
                for hour in hours[offset : offset + workers]
            ]
        for task in tasks:
            values, interval, mode, errors, absent = task.result()
            rows.extend(values)
            failed += errors
            missing += absent
            if interval is not None:
                received.append(interval)
                modes.add(mode)
        if len(rows) > MAX_DAILY_ROWS:
            raise ValueError("Dukascopy daily row limit exceeded")
    # Reference canonicalization keeps the first received row at each timestamp.
    unique: dict[int, tuple[Any, ...]] = {}
    for row in rows:
        unique.setdefault(row[0], row)
    ordered = [unique[key] for key in sorted(unique)]
    return DayFetch(
        _arrow_rows(ordered, dataset.kind),
        tuple(received),
        frozenset(modes),
        failed,
        missing,
        pa.concat_tables(provider_tables).sort_by("timestamp")
        if provider_tables
        else None,
    )


async def _fetch_day(
    network: NetworkAccess,
    dataset: MarketDataset,
    day: date,
    rate_corrector: RateCorrector | None = None,
) -> Any:
    """Preserve the existing CLI Arrow return contract for a single source day."""
    result = await _fetch_day_result(network, dataset, day, rate_corrector)
    return result.table


def _archive_stamp(name: str, kind: str) -> datetime | None:
    """Recognize source BI5 paths before interpreting their date and hour."""
    match = re.search(r"(\d{4})/(\d{2})/(\d{2})/(.*)\.bi5$", name)
    if match is None:
        return None
    member = match.group(4)
    if kind == "ticks":
        if not re.fullmatch(r"\d{2}h_ticks", member):
            return None
        hour = int(member[:2])
    elif "candles_min_1" in member:
        hour = 0
    else:
        return None
    year, month, day = (int(value) for value in match.groups()[:3])
    return datetime(year, month + 1, day, hour, tzinfo=UTC)


def _archive_selected(stamp: datetime, first: date | None, last: date | None) -> bool:
    """Select only request dates from an annual source archive."""
    return (first or date.min) <= stamp.date() <= (last or date.max)


async def _source_archive(  # noqa: C901, PLR0912 -- bounded monthly/annual and legacy transport paths.
    network: NetworkAccess,
    dataset: MarketDataset,
    year: int,
    mode: Literal["cdn", "cdn-cn"],
    *,
    archive_network: SourceNetwork | None = None,
    first: date | None = None,
    last: date | None = None,
    monthly: bool = True,
) -> dict[datetime, bytes]:
    """Read annual BI5 members using the owner's CDN archive/date convention."""
    result: dict[datetime, bytes] = {}
    if archive_network is not None:
        keys = [str(year)]
        if monthly and first is not None and last is not None:
            keys = [
                f"{year}_{month:02d}"
                for month in range(1, 13)
                if date(year, month, 1) <= last
                and (year, month) >= (first.year, first.month)
            ]
        urls = [
            _cdn_archive_url(mode, dataset.kind, dataset.symbol.upper(), key)
            for key in keys
        ]
        missing_month = False
        size = 0
        for url in urls:
            if (await archive_network.head(url)).status != HTTP_OK:
                missing_month = True
                continue
            async with archive_network.archive(url) as archive:
                for name in archive.members():
                    stamp = _archive_stamp(name, dataset.kind)
                    if stamp is None or not _archive_selected(stamp, first, last):
                        continue
                    content = archive.read(name)
                    size += len(content)
                    if size > MAX_DECOMPRESSED:
                        raise ValueError(
                            "Selected Dukascopy archive chunks exceed job bounds"
                        )
                    result.setdefault(stamp, content)
        if missing_month and keys != [str(year)]:
            annual = await _source_archive(
                network,
                dataset,
                year,
                mode,
                archive_network=archive_network,
                first=first,
                last=last,
                monthly=False,
            )
            for stamp, content in annual.items():
                if stamp not in result and _archive_selected(stamp, first, last):
                    size += len(content)
                    if size > MAX_DECOMPRESSED:
                        raise ValueError(
                            "Selected Dukascopy archive chunks exceed job bounds"
                        )
                    result[stamp] = content
        if not result:
            logger.info("Dukascopy CDN unavailable; direct chunks remain eligible")
        logger.info("Dukascopy spooled archive read: chunks=%d", len(result))
        return result
    response = await network.get(
        _cdn_archive_url(mode, dataset.kind, dataset.symbol.upper(), str(year))
    )
    if response.status != HTTP_OK or not response.body:
        logger.info("Dukascopy CDN archive unavailable; using direct chunks")
        return {}
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        if sum(info.file_size for info in archive.infolist()) > MAX_DECOMPRESSED:
            raise ValueError("Dukascopy archive exceeds its expansion limit")
        for member in archive.infolist():
            stamp = _archive_stamp(member.filename, dataset.kind)
            if stamp is None:
                continue
            result.setdefault(stamp, archive.read(member))
    logger.info("Dukascopy CDN archive decoded: year=%d chunks=%d", year, len(result))
    return result


async def _prepare(context: HostCapabilities) -> PreparedContribution:  # noqa: C901, PLR0915 -- single cohesive acquisition concept.
    """Bind direct acquisition to declared host market, network and job services."""
    if context.market_data is None or context.network is None or context.jobs is None:
        raise ValueError("Dukascopy host capabilities unavailable")
    if (
        context.resources is None
        or context.resources.owner != PLUGIN["id"]
        or context.resources.version != PLUGIN["version"]
    ):
        raise ValueError(
            "Dukascopy result resource capability unavailable or incompatible"
        )
    market = context.market_data
    network = context.network
    jobs = context.jobs
    archive_network = context.network.source_session(
        ("https://cdn.strategyquantcdn.com", "https://cdn005.strategyquantcdn.com")
    )
    results: dict[str, dict[str, JsonValue]] = {}
    request_by_job: dict[str, str] = {}
    result_resources: dict[str, list[tuple[ResourceRef, int, bool]]] = {}
    logger.info("Preparing Dukascopy data source plugin")

    def publish_result(
        request_id: str, table: Any, dataset: MarketDataset, *, provider: bool
    ) -> None:
        """Publish bounded immutable pages with inert schema and chunk provenance."""
        if context.resources is None:
            raise ValueError("Dukascopy result resource capability unavailable")
        schema_id = (
            "dukascopy.provider_" + ("ticks" if dataset.kind == "ticks" else "m1")
            if provider
            else "dukascopy.canonical_" + dataset.kind
        )
        for offset in range(0, table.num_rows, RESULT_RESOURCE_ROWS):
            if len(result_resources[request_id]) >= MAX_RESULT_RESOURCES:
                raise ValueError("Dukascopy result resource limit reached")
            chunk = table.slice(offset, RESULT_RESOURCE_ROWS)
            sink = pa.BufferOutputStream()
            with pa.ipc.new_stream(sink, chunk.schema) as writer:
                writer.write_table(chunk)
            timestamp = "timestamp" if provider else "DateTime"
            times = chunk.column(timestamp).cast(pa.int64())
            schema = json.dumps(
                {
                    "schema_id": schema_id,
                    "schema_version": "1.0.0",
                    "dataset_id": dataset.id,
                    "kind": dataset.kind,
                    "request_id": request_id,
                    "representation": "provider" if provider else "canonical",
                    "start_ms": times[0].as_py(),
                    "day": datetime.fromtimestamp(times[0].as_py() / 1000, tz=UTC)
                    .date()
                    .isoformat(),
                    "end_ms": times[-1].as_py(),
                    "fields": [
                        {"name": field.name, "type": str(field.type)}
                        for field in chunk.schema
                    ],
                },
                sort_keys=True,
            )
            ref = context.resources.publish(
                sink.getvalue().to_pybytes(),
                schema_id=schema_id,
                schema_version="1.0.0",
                schema_json=schema,
                media_type="application/vnd.apache.arrow.stream",
                readers=("*",),
            )
            result_resources[request_id].append((ref, chunk.num_rows, provider))

    def retain_day_result(
        request_id: str,
        spec: DownloadSpec,
        dataset: MarketDataset,
        stamp: date,
        fetched: DayFetch | None,
    ) -> None:
        """Keep raw received rows and honestly identified canonical existing rows."""
        if spec.result_representation != "provider":
            return
        raw = fetched.provider_table if fetched is not None else None
        raw_times: set[int] = set()
        if raw is not None:
            # Source keeps one row per timestamp before returning its result.
            frame = raw.to_pandas().drop_duplicates("timestamp", keep="first")
            raw = pa.Table.from_pandas(frame, schema=raw.schema, preserve_index=False)
            raw_times = set(raw.column("timestamp").cast(pa.int64()).to_pylist())
            publish_result(request_id, raw, dataset, provider=True)
        if not spec.overwrite:
            first_ms = max(
                spec.start_ms,
                int(
                    datetime.combine(stamp, datetime.min.time(), tzinfo=UTC).timestamp()
                    * 1000
                ),
            )
            last_ms = min(spec.end_ms, first_ms - first_ms % DAY_MS + DAY_MS - 1)
            offset = 0
            while True:
                table = market.read_market_rows(
                    dataset.id,
                    start_ms=first_ms,
                    end_ms=last_ms,
                    offset=offset,
                    limit=RESULT_PAGE_ROWS,
                )
                count = table.num_rows
                if count:
                    times = table.column("DateTime").cast(pa.int64()).to_pylist()
                    table = table.filter(
                        pa.array([value not in raw_times for value in times])
                    )
                    publish_result(request_id, table, dataset, provider=False)
                if count < RESULT_PAGE_ROWS:
                    break
                offset += count

    async def run_download(  # noqa: C901, PLR0912, PLR0915 -- finite ordered source batches.
        request_id: str, spec: DownloadSpec, dataset: MarketDataset
    ) -> None:
        """Publish finite day batches while retaining partial source results."""
        result = results[request_id]
        info = _get_symbol_info(dataset.symbol)
        inception = info.m1_start if dataset.kind == "m1" else info.tick_start
        first = max(spec.first, inception) if inception else spec.first
        days = max(0, (spec.last - first).days + 1)
        corrector = RateCorrector()
        used_modes: set[str] = set()
        logger.info(
            "Starting Dukascopy download: symbol=%s kind=%s from=%s to=%s workers=%d",
            dataset.symbol,
            dataset.kind,
            first,
            spec.last,
            spec.workers,
        )
        result["effective_mode"] = "pending"
        result["date_from"] = first.isoformat()
        result["total_days"] = days
        archive: dict[datetime, bytes] = {}
        window: tuple[int, int] | None = None

        async def fetch(day: date) -> tuple[date, str, DayFetch | None]:
            if (
                day.weekday() == SATURDAY_WEEKDAY
                and "crypto" not in info.category.lower()
                and not spec.include_weekends
            ):
                return day, "skipped", None
            start_ms = max(
                int(
                    datetime.combine(day, datetime.min.time(), tzinfo=UTC).timestamp()
                    * 1000
                ),
                spec.start_ms,
            )
            end_ms = min(
                int(
                    datetime.combine(
                        day + timedelta(days=1), datetime.min.time(), tzinfo=UTC
                    ).timestamp()
                    * 1000
                )
                - 1,
                spec.end_ms,
            )
            period = (
                f"{day.year:04d}"
                if dataset.kind == "m1"
                else f"{day.year:04d}-{day.month:02d}"
            )
            existing = next(
                (
                    record
                    for record in market.list_files(
                        "dukascopy", dataset.kind, dataset.symbol
                    )
                    if record.period == period
                ),
                None,
            )
            coverage = existing.coverage if existing and not spec.overwrite else ()
            if any(left <= start_ms and end_ms <= right for left, right in coverage):
                return day, "skipped", None
            fetched = await _fetch_day_result(
                network,
                dataset,
                day,
                corrector,
                archive=archive if spec.candle_type == "BID" else {},
                archive_mode=spec.mode,
                skip_intervals=coverage,
                workers=spec.workers if dataset.kind == "ticks" else 1,
                start_ms=start_ms,
                end_ms=end_ms,
                candle_type=spec.candle_type,
                provider_results=spec.result_representation == "provider",
            )
            return day, period, fetched

        offset = 0
        while offset < days:
            day = first + timedelta(days=offset)
            current_window = (day.year, day.month)
            if spec.mode != "standard" and current_window != window:
                archive.clear()
                # Select one month from a host-spooled annual archive. The helper
                # keeps monthly-first compatibility for its existing callers.
                month_end = (day.replace(day=28) + timedelta(days=4)).replace(
                    day=1
                ) - timedelta(days=1)
                try:
                    archive = await _source_archive(
                        network,
                        dataset,
                        day.year,
                        spec.mode,
                        archive_network=archive_network,
                        first=day,
                        last=min(month_end, spec.last),
                        monthly=False,
                    )
                except (
                    NetworkUnavailableError,
                    httpx.HTTPError,
                    zipfile.BadZipFile,
                ) as error:
                    logger.warning(
                        "Dukascopy CDN unavailable; direct fallback: %s",
                        type(error).__name__,
                    )
                except ValueError as error:
                    if str(error).startswith(
                        (
                            "Selected Dukascopy archive chunks exceed",
                            "Archive request failed",
                            "Archive member",
                            "Source response exceeds",
                        )
                    ):
                        logger.warning("Dukascopy CDN bounds reached; direct fallback")
                    else:
                        raise
                window = current_window
            width = spec.workers if dataset.kind == "m1" else 1
            selected = []
            for step in range(width):
                if offset + step >= days:
                    break
                candidate = first + timedelta(days=offset + step)
                if (candidate.year, candidate.month) != current_window:
                    break
                selected.append(candidate)
            async with asyncio.TaskGroup() as group:
                tasks = [group.create_task(fetch(candidate)) for candidate in selected]
            for task in tasks:
                stamp, period, fetched = task.result()
                retain_day_result(request_id, spec, dataset, stamp, fetched)
                if fetched is None:
                    result["skipped_days"] = (
                        cast("int", result.get("skipped_days", 0)) + 1
                    )
                else:
                    used_modes.update(fetched.modes)
                    result["failed_chunks"] = (
                        cast("int", result.get("failed_chunks", 0))
                        + fetched.failed_chunks
                    )
                    result["missing_chunks"] = (
                        cast("int", result.get("missing_chunks", 0))
                        + fetched.missing_chunks
                    )
                    result["effective_mode"] = (
                        next(iter(used_modes))
                        if len(used_modes) == 1
                        else "mixed"
                        if used_modes
                        else "none"
                    )
                    if fetched.table.num_rows:
                        start_ms = max(
                            int(
                                datetime.combine(
                                    stamp, datetime.min.time(), tzinfo=UTC
                                ).timestamp()
                                * 1000
                            ),
                            spec.start_ms,
                        )
                        end_ms = min(
                            start_ms - start_ms % DAY_MS + DAY_MS - 1, spec.end_ms
                        )
                        market.replace_interval(
                            kind=dataset.kind,
                            symbol=dataset.symbol,
                            period=period,
                            incoming=fetched.table,
                            start_ms=start_ms,
                            end_ms=end_ms,
                            mode=str(result["effective_mode"]),
                            received_intervals=fetched.received_intervals,
                            merge_timestamps=True,
                        )
                        result["published_days"] = (
                            cast("int", result.get("published_days", 0)) + 1
                        )
                    else:
                        result["missing_days"] = (
                            cast("int", result.get("missing_days", 0)) + 1
                        )
                offset += 1
                result["completed_days"] = offset
                result["progress"] = offset / days
        result["progress"] = 1.0
        result["outcome"] = (
            "partial"
            if cast("int", result.get("failed_chunks", 0))
            or cast("int", result.get("missing_days", 0))
            else "complete"
        )
        if not cast("int", result.get("published_days", 0)) and not cast(
            "int", result.get("skipped_days", 0)
        ):
            result["outcome"] = "empty"
        logger.info(
            "Completed Dukascopy download: symbol=%s outcome=%s "
            "published=%s failed_chunks=%s",
            dataset.symbol,
            result["outcome"],
            result.get("published_days", 0),
            result.get("failed_chunks", 0),
        )

    async def invoke(operation: str, payload: JsonValue) -> JsonValue:  # noqa: C901, PLR0911, PLR0912, PLR0915
        """Dispatch dataset, job and catalog requests through owner capabilities."""
        logger.info("Dukascopy plugin invoking operation: %s", operation)
        if operation == "catalog":
            try:
                brokers: list[JsonValue] = [
                    {
                        "id": broker.id,
                        "name": broker.name,
                        "postfix": broker.postfix,
                        "timezone": broker.timezone,
                        "mtUse": True,
                        "instruments": [],
                    }
                    for broker in market.list_brokers()
                ]
                broker_catalog_status = "available"
            except ValueError:
                brokers = []
                broker_catalog_status = "unavailable"
            return {
                "source": "dukascopy",
                "market_root": market.market_root(),
                "formats": ["ticks", "m1"],
                "brokers": brokers,
                "broker_catalog_status": broker_catalog_status,
                "definitions_available": market.definitions_available(),
                "modes": {
                    "standard": "available" if market.available() else "unavailable",
                    "cdn": "available" if market.available() else "unavailable",
                    "cdn-cn": "available" if market.available() else "unavailable",
                },
                "reason": "market_catalog_migration_required"
                if not market.available()
                else "ready",
                "datasets": list(market.list_datasets())
                if market.definitions_available()
                else [],
            }
        if operation == "definitions.add":
            if not isinstance(payload, dict) or not isinstance(
                payload.get("symbols"), list
            ):
                raise ValueError("Invalid dataset batch")
            symbols = payload.get("symbols")
            if not isinstance(symbols, list):
                raise TypeError("Invalid dataset symbols")
            kind = payload.get("kind")
            broker = payload.get("broker", "-1")
            postfix = payload.get("postfix", "")
            instruments = payload.get("instruments", [])
            if (
                kind not in ("m1", "ticks")
                or not isinstance(broker, str)
                or not isinstance(postfix, str)
                or not isinstance(instruments, list)
                or len(instruments) not in (0, len(symbols))
            ):
                raise ValueError("Invalid dataset batch")
            requests: list[DefinitionRequest] = []
            for index, symbol in enumerate(symbols):
                instrument = instruments[index] if instruments else "-1"
                if not isinstance(symbol, str) or not isinstance(instrument, str):
                    raise TypeError("Invalid dataset symbol or instrument")
                requests.append(
                    DefinitionRequest(
                        symbol,
                        "m1" if kind == "m1" else "ticks",
                        broker,
                        postfix,
                        instrument,
                    )
                )
            logger.info(
                "Registering %d Dukascopy dataset definitions (kind=%s, broker=%s)",
                len(requests),
                kind,
                broker,
            )
            return {
                "ids": [
                    row.id
                    for row in market.register_definitions(
                        tuple(requests), idempotent=True
                    )
                ]
            }
        if not market.available():
            raise ValueError("Market catalog migration is required")
        if operation == "add":
            if not isinstance(payload, dict):
                raise ValueError("Invalid Dukascopy dataset request")
            symbol = payload.get("symbol")
            kind = payload.get("kind", "m1")
            instrument = payload.get("instrument", symbol)
            if not isinstance(symbol, str) or not isinstance(instrument, str):
                raise ValueError("Invalid Dukascopy dataset request")
            _point_value(symbol)
            if kind not in ("ticks", "m1"):
                raise ValueError("Invalid Dukascopy data kind")
            k: Literal["ticks", "m1"] = "ticks" if kind == "ticks" else "m1"
            ds = market.register_dataset(symbol.lower(), k, instrument)
            logger.info("Adding Dukascopy dataset %s (%s)", symbol, k)
            return {
                "id": ds.id,
                "source": ds.source,
                "symbol": ds.symbol,
                "kind": ds.kind,
                "instrument": ds.instrument,
                "broker": ds.broker,
                "timezone": ds.timezone,
            }
        if operation == "disclaimer":
            return {
                "dukascopy_disclaimer": DUKASCOPY_DISCLAIMER_TEXT,
                "cdn_disclaimer": CDN_DISCLAIMER_TEXT,
            }
        if operation in ("download.start", "import"):
            spec = _spec(payload)
            if spec.result_representation == "provider" and context.resources is None:
                raise ValueError("Dukascopy result resource capability unavailable")
            dataset = market.get_dataset(spec.dataset_id)
            _point_value(dataset.symbol.upper())
            request_id = uuid4().hex
            result_resources[request_id] = []
            results[request_id] = {
                "requested_mode": spec.mode,
                "effective_mode": spec.mode,
                "completed_days": 0,
                "published_days": 0,
                "missing_days": 0,
                "skipped_days": 0,
                "progress": 0.0,
                "failed_chunks": 0,
                "missing_chunks": 0,
                "outcome": "pending",
                "dataset_id": dataset.id,
                "result_representation": spec.result_representation,
            }

            async def body() -> None:
                try:
                    await run_download(request_id, spec, dataset)
                except ValueError, ExceptionGroup:
                    results[request_id]["error"] = (
                        "Download stopped by validation or custody failure; "
                        "already committed rows were retained."
                    )
                    raise

            job = jobs.submit(
                Budget(
                    workers=1,
                    memory_bytes=128 * 1024 * 1024,
                    timeout_seconds=min(
                        604800, max(7200, ((spec.last - spec.first).days + 1) * 300)
                    ),
                ),
                body,
            )
            request_by_job[job.id] = request_id
            logger.info(
                "Submitted Dukascopy download job %s for dataset %s (request_id=%s)",
                job.id,
                spec.dataset_id,
                request_id,
            )
            return {
                "job_id": job.id,
                "request_id": request_id,
                "requested_mode": spec.mode,
                "effective_mode": spec.mode,
            }
        if operation in ("download.status", "download.cancel"):
            if not isinstance(payload, dict) or not isinstance(
                payload.get("job_id"), str
            ):
                raise ValueError("Invalid Dukascopy job request")
            job_id_val = payload["job_id"]
            if not isinstance(job_id_val, str) or job_id_val not in request_by_job:
                raise ValueError("Dukascopy job unavailable")
            if operation == "download.cancel":
                jobs.cancel(job_id_val)
                logger.info("Cancelled Dukascopy download job %s", job_id_val)
            job = jobs.status(job_id_val)
            return {
                "job_id": job.id,
                "state": job.state,
                **results[request_by_job[job_id_val]],
            }
        if operation == "download.results.read":
            if not isinstance(payload, dict):
                raise ValueError("Invalid result read request")
            job_id = payload.get("job_id")
            offset, limit = (
                payload.get("offset", 0),
                payload.get("limit", RESULT_PAGE_ROWS),
            )
            if (
                not isinstance(job_id, str)
                or job_id not in request_by_job
                or type(offset) is not int
                or type(limit) is not int
                or offset < 0
                or not 1 <= limit <= RESULT_PAGE_ROWS
            ):
                raise ValueError("Invalid result read bounds")
            if context.resources is None:
                raise ValueError("Dukascopy result resource capability unavailable")
            request_id = request_by_job[job_id]
            if results[request_id]["result_representation"] != "provider":
                raise ValueError("Job did not request provider results")
            remaining = offset
            for ref, count, provider in result_resources[request_id]:
                if remaining >= count:
                    remaining -= count
                    continue
                content, schema_json = context.resources.read(ref)
                schema = json.loads(schema_json)
                if (
                    ref.producer_id != PLUGIN["id"]
                    or ref.producer_version != PLUGIN["version"]
                    or ref.schema_version != "1.0.0"
                    or schema.get("request_id") != request_id
                    or schema.get("schema_id") != ref.schema_id
                    or schema.get("schema_version") != ref.schema_version
                    or schema.get("dataset_id") != results[request_id]["dataset_id"]
                    or ref.media_type != "application/vnd.apache.arrow.stream"
                ):
                    raise ValueError("Invalid Dukascopy result provenance")
                table = pa.ipc.open_stream(content).read_all()
                kind = schema["kind"]
                expected = (
                    (PROVIDER_TICK_SCHEMA if kind == "ticks" else PROVIDER_M1_SCHEMA)
                    if provider
                    else (TICK_SCHEMA if kind == "ticks" else M1_SCHEMA)
                )
                if (
                    not table.schema.equals(expected, check_metadata=False)
                    or table.num_rows != count
                    or schema.get("fields")
                    != [
                        {"name": field.name, "type": str(field.type)}
                        for field in expected
                    ]
                ):
                    raise ValueError("Invalid Dukascopy result schema")
                timestamps = table.column("timestamp" if provider else "DateTime").cast(
                    pa.int64()
                )
                if (
                    schema.get("start_ms") != timestamps[0].as_py()
                    or schema.get("end_ms") != timestamps[-1].as_py()
                    or schema.get("representation")
                    != ("provider" if provider else "canonical")
                ):
                    raise ValueError("Invalid Dukascopy result range or representation")
                table = table.slice(remaining, limit)
                frame = table.to_pandas()
                if not provider:
                    frame = frame.rename(
                        columns={
                            "DateTime": "timestamp",
                            "Open": "open",
                            "High": "high",
                            "Low": "low",
                            "Close": "close",
                            "Volume": "volume",
                            "Ask": "ask",
                            "Bid": "bid",
                        }
                    )
                    if kind == "ticks":
                        frame["ask"] = frame["ask"] / 1_000_000
                        frame["bid"] = frame["bid"] / 1_000_000
                        frame["ask_volume"] = frame["volume"]
                        frame["bid_volume"] = frame.pop("volume")
                dtypes = {
                    name: str(dtype)
                    for name, dtype in frame.dtypes.items()
                    if name != "timestamp"
                }
                frame["timestamp"] = frame["timestamp"].map(
                    lambda value: value.isoformat()
                )
                result_rows = frame.to_dict(orient="records")
                next_offset = offset + len(result_rows)
                return {
                    "rows": result_rows,
                    "dtypes": dtypes,
                    "origin": "provider" if provider else "canonical",
                    "day": schema["day"],
                    "next_offset": next_offset,
                    "has_more": next_offset
                    < sum(item[1] for item in result_resources[request_id]),
                }
            return {"rows": [], "dtypes": {}, "next_offset": offset, "has_more": False}
        if operation == "rows.read":
            if not isinstance(payload, dict):
                raise TypeError("Invalid market read request")
            dataset_id = payload.get("dataset_id")
            first_ms, last_ms = payload.get("start_ms"), payload.get("end_ms")
            offset, limit = payload.get("offset", 0), payload.get("limit", 2000)
            if not isinstance(dataset_id, str) or any(
                type(value) is not int for value in (first_ms, last_ms, offset, limit)
            ):
                raise TypeError("Invalid market read bounds")
            table = market.read_market_rows(
                dataset_id,
                start_ms=cast("int", first_ms),
                end_ms=cast("int", last_ms),
                offset=cast("int", offset),
                limit=cast("int", limit),
            )
            rows: list[JsonValue] = []
            for record in table.to_pylist():
                record["DateTime"] = record["DateTime"].isoformat()
                rows.append(record)
            return {
                "rows": rows,
                "next_offset": cast("int", offset) + len(rows),
                "has_more": len(rows) == limit,
            }
        if operation == "files.list":
            if not isinstance(payload, dict):
                raise ValueError("Invalid market listing request")
            symbol = payload.get("symbol")
            kind = payload.get("kind")
            if not isinstance(symbol, str) or not isinstance(kind, str):
                raise ValueError("Invalid market listing request")
            return [
                vars(item)
                for item in market.list_files("dukascopy", kind, symbol.lower())
            ]
        if operation == "delete":
            if not isinstance(payload, dict):
                raise ValueError("Invalid delete payload")
            sym = payload.get("symbol")
            if not isinstance(sym, str):
                raise ValueError("Invalid delete payload")
            deleted = market.delete_dataset(sym)
            logger.info("Deleting Dukascopy dataset %s (deleted=%s)", sym, deleted)
            return {"deleted": deleted, "symbol": sym}
        if operation == "clear":
            if not isinstance(payload, dict):
                raise ValueError("Invalid clear payload")
            sym = payload.get("symbol")
            if not isinstance(sym, str):
                raise ValueError("Invalid clear payload")
            cleared = market.clear_dataset(sym)
            logger.info("Clearing Dukascopy dataset %s (cleared=%s)", sym, cleared)
            return {"cleared": cleared, "symbol": sym}
        logger.warning("Missing Dukascopy operation: %s", operation)
        raise ValueError("Missing Dukascopy operation")

    async def close() -> None:
        """Release local result references; the host owns task cancellation."""
        await jobs.close()
        await archive_network.close()
        results.clear()
        request_by_job.clear()
        result_resources.clear()
        logger.info("Dukascopy data source plugin closed")

    return PreparedContribution(
        (
            "catalog",
            "definitions.add",
            "add",
            "download.start",
            "download.status",
            "download.cancel",
            "download.results.read",
            "import",
            "disclaimer",
            "files.list",
            "rows.read",
            "delete",
            "clear",
        ),
        invoke,
        close,
    )


def _client(
    client: Client | None = None,
    *,
    url: str = "http://127.0.0.1:8000",
    username: str = "operator",
    quiet: bool = False,
) -> Client:
    """Connect through the universal CLI handshake, retaining host authority."""
    if client is not None:
        return client
    result = Client(url)
    result.initialize(
        username,
        os.environ.get("HARU_CLIENT_PASSWORD"),
        output=io.StringIO() if quiet else sys.stderr,
    )
    return result


def _invoke(client: Client, operation: str, payload: dict[str, Any]) -> Any:
    """Call the same owner route used by the paired UI."""
    logger.info("Dukascopy client invoking: %s", operation)
    return client.request(
        "/contributions/workspace.data_manager/sources.dukascopy." + operation, payload
    )


def _symbol(symbol: str) -> str:
    """Normalize source aliases and broker postfix without changing provider ID."""
    clean = (
        symbol.strip()
        .upper()
        .replace("_DUKASCOPY", "")
        .replace("-", "")
        .replace("/", "")
    )
    _symbol_decimals(clean)
    return clean


def _kinds(value: str) -> tuple[Literal["m1", "ticks"], ...]:
    """Interpret the source's M1/TICK/both aliases."""
    clean = value.strip().upper()
    m1 = "M1" in clean or clean in ("CANDLES", "ALL", "BOTH")
    ticks = "TICK" in clean or clean in ("ALL", "BOTH")
    return ("m1", "ticks") if m1 and ticks else ("ticks",) if ticks else ("m1",)


def add_symbol(
    source: str = "dukascopy",
    symbol: str = "GBPUSD",
    data_type: str = "M1",
    broker: str = "dukascopy",
    disclaimer: bool = True,
    *,
    client: Client | None = None,
) -> str | list[str]:
    """Register through UI definitions.add, resolving actual broker metadata."""
    if source != "dukascopy":
        raise ValueError("This provider cannot write another source namespace")
    connection = _client(client)
    catalog = _invoke(connection, "catalog", {})
    if not catalog["definitions_available"]:
        raise ClientError("Dataset catalog is unavailable")
    if broker.strip().lower() in ("-1", "default"):
        broker_id, postfix = "-1", ""
    else:
        clean_broker = (
            broker.lower().strip().replace("[[", "").replace("]]", "").replace("_", "")
        )
        matches = [
            row
            for row in catalog["brokers"]
            if clean_broker in row["name"].lower().replace("_", "")
            or clean_broker in row["postfix"].lower().replace("_", "")
            or broker == row["id"]
        ]
        if len(matches) != 1:
            raise ClientError("Choose an existing unambiguous broker profile")
        broker_id, postfix = matches[0]["id"], matches[0]["postfix"]
    clean_symbol = _symbol(
        symbol.upper().replace(postfix.upper(), "") if postfix else symbol
    )
    if disclaimer:
        logger.info("Dukascopy disclaimer acknowledged: data provided AS IS")
    ids: list[str] = []
    for kind in _kinds(data_type):
        result = _invoke(
            connection,
            "definitions.add",
            {
                "symbols": [clean_symbol],
                "kind": kind,
                "broker": broker_id,
                "postfix": postfix,
                "instruments": [],
            },
        )
        ids.extend(result["ids"])
    return ids[0] if len(ids) == 1 else ids


def _download_jobs(
    client: Client,
    symbols: str | list[str],
    start: str | date | datetime,
    end: str | date | datetime,
    *,
    data_type: str,
    redownload: str,
    cdn: str,
    workers: int,
    include_weekends: bool,
    candle_type: str = "BID",
    result_representation: str = "canonical",
) -> dict[str, dict[str, Any]]:
    """Submit and await host-owned jobs; interruption cancels the current job."""
    selection = symbols.split(",") if isinstance(symbols, str) else symbols
    mode = (
        "cdn-cn"
        if cdn.upper() in ("CHINA", "HK", "HONGKONG")
        else "cdn"
        if cdn.upper() in ("SQX", "CLOUDFLARE")
        else "standard"
    )
    results: dict[str, dict[str, Any]] = {}
    for symbol in selection:
        clean = _symbol(symbol)
        for kind in _kinds(data_type):
            catalog = _invoke(client, "catalog", {})
            matches = [
                row
                for row in catalog["datasets"]
                if row.get("underlying", row["symbol"]).upper() == clean
                and row["timeframe"] == ("M1" if kind == "m1" else "TICK")
            ]
            if len(matches) > 1:
                raise ClientError(
                    "Multiple dataset definitions match; select a unique broker "
                    "definition"
                )
            dataset_id = (
                matches[0]["id"]
                if matches
                else add_symbol(symbol=clean, data_type=kind, client=client)
            )
            started = _invoke(
                client,
                "download.start",
                {
                    "dataset_id": dataset_id,
                    "date_from": _parse_datetime(start).isoformat(),
                    "date_to": _parse_datetime(end, True).isoformat(),
                    "overwrite": redownload.upper() in ("OVERWRITE", "FORCE"),
                    "mode": mode,
                    "workers": workers,
                    "include_weekends": include_weekends,
                    "candle_type": candle_type,
                    "result_representation": result_representation,
                },
            )
            try:
                while True:
                    status = _invoke(
                        client, "download.status", {"job_id": started["job_id"]}
                    )
                    if status["state"] not in ("queued", "running"):
                        break
                    time.sleep(0.2)
            except KeyboardInterrupt, OSError, ClientError:
                _invoke(client, "download.cancel", {"job_id": started["job_id"]})
                raise
            if status["state"] != "succeeded":
                raise ClientError("Dukascopy host job " + status["state"])
            results[clean + ("_M1" if kind == "m1" else "_TICKS")] = {
                "dataset_id": dataset_id,
                **status,
            }
    return results


def _row_frames(
    client: Client,
    dataset_id: str,
    start: str | date | datetime,
    end: str | date | datetime,
    *,
    tz: str | None = None,
    lower: bool = False,
    ticks: bool = False,
) -> Iterator[Any]:
    """Yield verified pages; timezone conversion affects presentation only."""
    first = int(_parse_datetime(start).timestamp() * 1000)
    last = int(_parse_datetime(end, True).timestamp() * 1000)
    offset = 0
    while True:
        result = _invoke(
            client,
            "rows.read",
            {
                "dataset_id": dataset_id,
                "start_ms": first,
                "end_ms": last,
                "offset": offset,
                "limit": 2000,
            },
        )
        if result["rows"]:
            frame = pd.DataFrame(result["rows"])
            frame["Volume"] = frame["Volume"].astype("uint64")
            for name in ("Open", "High", "Low", "Close"):
                if name in frame:
                    frame[name] = frame[name].astype("float64")
            frame["DateTime"] = pd.to_datetime(frame["DateTime"], utc=True).dt.as_unit(
                "ms"
            )
            if tz:
                frame["DateTime"] = frame["DateTime"].dt.tz_convert(tz)
            if lower:
                frame = frame.rename(
                    columns={
                        "DateTime": "timestamp",
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Volume": "volume",
                        "Ask": "ask",
                        "Bid": "bid",
                    }
                )
                if ticks:
                    frame["ask"] = frame["ask"] / 1_000_000
                    frame["bid"] = frame["bid"] / 1_000_000
            yield frame
        if not result["has_more"]:
            break
        if result["next_offset"] <= offset:
            raise ClientError("Host returned a non-advancing market page")
        offset = result["next_offset"]


def _canonical_result_frames(
    client: Client,
    job: dict[str, Any],
    start: str | date | datetime,
    end: str | date | datetime,
    *,
    ticks: bool,
    tz: str | None = None,
) -> Iterator[Any]:
    """Match the reference's store-enabled return columns and integer volumes."""
    for frame in _row_frames(
        client, job["dataset_id"], start, end, tz=tz, lower=True, ticks=ticks
    ):
        if ticks:
            frame["ask_volume"] = frame["volume"]
            frame["bid_volume"] = frame.pop("volume")
        yield frame


def _result_frames(  # noqa: C901 -- bounded typed page/day reconstruction.
    client: Client, job_id: str, *, tz: str | None = None, export: bool = False
) -> Iterator[Any]:
    """Read verified bounded provider/canonical pages with explicit numeric types."""
    offset = 0
    day: str | None = None
    day_frames: list[Any] = []
    day_bytes = 0
    while True:
        page = _invoke(
            client,
            "download.results.read",
            {"job_id": job_id, "offset": offset, "limit": RESULT_PAGE_ROWS},
        )
        if page["rows"]:
            frame = pd.DataFrame(page["rows"])
            frame["timestamp"] = pd.to_datetime(
                frame["timestamp"], utc=True
            ).dt.as_unit("ms")
            for name, dtype in page["dtypes"].items():
                if dtype not in ("float32", "float64", "uint64", "int64"):
                    raise ClientError("Unsupported provider result numeric type")
                frame[name] = frame[name].astype(dtype)
                if export and name in ("volume", "ask_volume", "bid_volume"):
                    # One stable file schema across raw and reconstructed chunks.
                    frame[name] = frame[name].astype("float64")
            if tz:
                frame["timestamp"] = frame["timestamp"].dt.tz_convert(tz)
            current_day = page.get(
                "day", frame["timestamp"].iloc[0].tz_convert("UTC").date().isoformat()
            )
            if day_frames and current_day != day:
                yield (
                    pd.concat(day_frames, ignore_index=True)
                    .sort_values("timestamp")
                    .drop_duplicates("timestamp", keep="first")
                    .reset_index(drop=True)
                )
                day_frames.clear()
                day_bytes = 0
            day = current_day
            day_bytes += int(frame.memory_usage(deep=True).sum())
            if day_bytes > 128 * 1024 * 1024:
                raise ClientError("Provider result day exceeds client memory bounds")
            day_frames.append(frame)
        if not page["has_more"]:
            break
        if page["next_offset"] <= offset:
            raise ClientError("Host returned a non-advancing result page")
        offset = page["next_offset"]
    if day_frames:
        yield (
            pd.concat(day_frames, ignore_index=True)
            .sort_values("timestamp")
            .drop_duplicates("timestamp", keep="first")
            .reset_index(drop=True)
        )


def download_data(  # noqa: PLR0917 -- reference public signature.
    symbols: str | list[str],
    start_date: str | date | datetime,
    end_date: str | date | datetime,
    redownload: str = "MISSING",
    source: str = "dukascopy",
    cdn: str = "STANDARD",
    data_type: str = "M1",
    *,
    workers: int = 4,
    store: str | Path | bool = "data/market",
    show_progress: bool = True,
    ignore_weekends: bool = True,
    tz: str | None = None,
    candle_type: str = "BID",
    client: Client | None = None,
    result_representation: str = "canonical",
) -> dict[str, Any]:
    """Download through host jobs and return source-shaped tabular results."""
    connection = _client(client)
    _validate_custody(connection, source, store)
    logger.info("Dukascopy download requested: progress=%s", show_progress)
    jobs = _download_jobs(
        connection,
        symbols,
        start_date,
        end_date,
        data_type=data_type,
        redownload=redownload,
        cdn=cdn,
        workers=workers,
        include_weekends=not ignore_weekends,
        candle_type=candle_type,
        result_representation=result_representation,
    )
    results: dict[str, Any] = {}
    for key, job in jobs.items():
        if result_representation == "provider":
            frames = list(_result_frames(connection, job["job_id"], tz=tz))
            frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            if not frame.empty:
                frame = (
                    frame.sort_values("timestamp")
                    .drop_duplicates("timestamp", keep="first")
                    .reset_index(drop=True)
                )
            results[key] = frame
            continue
        frames = list(
            _row_frames(
                connection,
                job["dataset_id"],
                start_date,
                end_date,
                tz=tz,
                lower=True,
                ticks=key.endswith("_TICKS"),
            )
        )
        frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if key.endswith("_TICKS") and not frame.empty:
            # Source missing-mode reads reconstruct both side volumes from custody.
            frame["ask_volume"] = frame["volume"]
            frame["bid_volume"] = frame["volume"]
            frame = frame.drop(columns=["volume"])
        results[key] = frame
    return results


def _validate_custody(client: Client, source: str, store: str | Path | bool) -> None:
    """Reject peer namespaces or a root that differs from host configuration."""
    if source != "dukascopy":
        raise ClientError("This provider cannot impersonate another source")
    if store is False:
        raise ClientError(
            "App acquisition uses durable host custody; transient store=False "
            "is unavailable"
        )
    root = _invoke(client, "catalog", {})["market_root"]
    if store is not True and Path(store).resolve() != Path(root).resolve():
        raise ClientError(
            "--store must match the running host's market root; configure the "
            "host data directory first"
        )


def _dashboard(
    source: str | None = "dukascopy",
    symbol: str | None = None,
    *,
    client: Client | None = None,
) -> list[dict[str, Any]]:
    """Return actual definition metadata without reading another provider's code."""
    connection = _client(client)
    if source is None:
        result = connection.request(
            "/contributions/workspace.data_manager/actions.list_datasets", {}
        )
        rows = result if isinstance(result, list) else result.get("datasets", [])
    elif source == "dukascopy":
        rows = _invoke(connection, "catalog", {})["datasets"]
    else:
        raise ClientError("Unknown dashboard source")
    logger.info("Dukascopy dashboard read: definitions=%d", len(rows))
    return [
        row
        for row in rows
        if symbol is None
        or symbol.upper() in (row["symbol"].upper(), row.get("underlying", "").upper())
    ]


def show_disclaimer() -> str:
    """Return the provider and CDN disclaimers without requiring a connection."""
    logger.info("Dukascopy disclaimers requested")
    return DUKASCOPY_DISCLAIMER_TEXT + "\n\n" + CDN_DISCLAIMER_TEXT


def _build_arg_parser() -> argparse.ArgumentParser:
    """Expose the source command syntax with explicit app-host connection options."""
    parser = argparse.ArgumentParser(
        description="HaruQuantAI Dukascopy Data Manager CLI"
    )
    commands = parser.add_subparsers(dest="subcommand")
    commands.add_parser("disclaimer")
    add = commands.add_parser("add-symbol")
    add.add_argument("--symbol", "-s", required=True)
    add.add_argument("--type", "-t", default="M1")
    add.add_argument("--broker", default="dukascopy")
    add.add_argument("--source", default="dukascopy")
    add.add_argument("--no-disclaimer", action="store_true")
    download = commands.add_parser("download")
    download.add_argument("--symbols", "--symbol", "-s", required=True)
    download.add_argument("--start", required=True)
    download.add_argument("--end", required=True)
    download.add_argument(
        "--redownload",
        choices=["MISSING", "OVERWRITE", "missing", "overwrite"],
        default="MISSING",
    )
    download.add_argument(
        "--cdn",
        choices=["STANDARD", "SQX", "CHINA", "standard", "sqx", "china"],
        default="STANDARD",
    )
    download.add_argument("--type", "-t", default="M1")
    download.add_argument("--source", default="dukascopy")
    download.add_argument("--timezone", "--tz")
    download.add_argument("--include-weekends", action="store_true")
    download.add_argument("--store", default="data/market")
    download.add_argument("--output", "-o")
    download.add_argument(
        "--result-representation",
        choices=("canonical", "provider"),
        default="canonical",
    )
    download.add_argument("--workers", "-w", type=int, default=4)
    download.add_argument("--quiet", "-q", action="store_true")
    view = commands.add_parser("dashboard")
    view.add_argument("--symbol", "-s")
    view.add_argument("--all", action="store_true")
    for command in (add, download, view):
        command.add_argument("--url", default="http://127.0.0.1:8000")
        command.add_argument("--username", default="operator")
    return parser


def _legacy_args(argv: list[str]) -> list[str]:
    """Translate source legacy flags into one validated modern command."""
    if not argv or not argv[0].startswith("-") or argv[0] in ("--help", "-h"):
        return argv
    if argv[0] in ("--dashboard", "-dashboard"):
        return ["dashboard", *argv[1:]]
    if argv[0] in ("--disclaimer", "-disclaimer"):
        return ["disclaimer", *argv[1:]]
    result = ["download"]
    index = 0
    while index < len(argv):
        value = argv[index]
        if value in ("--mode", "-m"):
            if index + 1 == len(argv):
                return [*result, "--redownload"]
            result.extend(["--redownload", argv[index + 1].upper()])
            index += 2
        elif value == "--overwrite":
            result.extend(["--redownload", "OVERWRITE"])
            index += 1
        elif value == "--no-cdn":
            result.extend(["--cdn", "STANDARD"])
            index += 1
        elif value == "--store" and (
            index + 1 == len(argv) or argv[index + 1].startswith("-")
        ):
            result.extend(["--store", "data/market"])
            index += 1
        else:
            result.append(value)
            index += 1
    return result


def _main(argv: list[str] | None = None) -> int:
    """Run provider commands through authenticated host operations."""
    parser = _build_arg_parser()
    args = parser.parse_args(_legacy_args(list(sys.argv[1:] if argv is None else argv)))
    if not args.subcommand:
        parser.print_help()
        return 0
    if args.subcommand == "disclaimer":
        sys.stdout.write(show_disclaimer() + "\n")
        return 0
    try:
        connection = _client(
            url=args.url, username=args.username, quiet=getattr(args, "quiet", False)
        )
        if args.subcommand == "add-symbol":
            result: Any = {
                "ids": add_symbol(
                    args.source,
                    args.symbol,
                    args.type,
                    args.broker,
                    not args.no_disclaimer,
                    client=connection,
                )
            }
        elif args.subcommand == "dashboard":
            result = _dashboard(
                None if args.all else "dukascopy", args.symbol, client=connection
            )
        else:
            _validate_custody(connection, args.source, args.store)
            result = _download_jobs(
                connection,
                args.symbols,
                args.start,
                args.end,
                data_type=args.type,
                redownload=args.redownload,
                cdn=args.cdn,
                workers=args.workers,
                include_weekends=args.include_weekends,
                result_representation=args.result_representation,
            )
            if args.output and result:
                key, job = next(iter(result.items()))
                if args.result_representation == "provider":
                    frames = _result_frames(
                        connection, job["job_id"], tz=args.timezone, export=True
                    )
                else:
                    frames = _canonical_result_frames(
                        connection,
                        job,
                        args.start,
                        args.end,
                        ticks=key.endswith("_TICKS"),
                        tz=args.timezone,
                    )
                write_table_output(Path(args.output), frames)
        sys.stdout.write(json.dumps(result) + "\n")
        if args.subcommand == "download" and any(
            job.get("outcome") in ("partial", "empty") for job in result.values()
        ):
            sys.stderr.write(
                "Download retained available rows; some requested chunks are "
                "unavailable. Rerun MISSING to retry.\n"
            )
            return 2
    except (OSError, ValueError, TimeoutError) as error:
        logger.error("Dukascopy CLI failed: %s", type(error).__name__)  # noqa: TRY400 -- omit credential-bearing diagnostics.
        sys.stderr.write(
            "Dukascopy command failed: "
            + (str(error) if isinstance(error, ClientError) else type(error).__name__)
            + ". Check the running app host and its catalog.\n"
        )
        return 1
    return 0


def _decompress_bi5(data: bytes) -> bytes:
    """Return decoded BI5 bytes, or an explicitly logged invalid empty result."""
    try:
        return _decompress(data, 1)
    except ValueError:
        logger.warning("Dukascopy BI5 decompression rejected invalid bytes")
        return b""


@dataclass(frozen=True)
class NetworkManager:
    """Source-compatible retrieval through an explicitly injected host transport."""

    network: NetworkAccess

    async def get(self, url: str) -> bytes | None:
        """Read using the source fallback policy without owning a global session."""
        logger.info("Dukascopy injected network read")
        payload, _ = await _direct_payload(self.network, url, RateCorrector())
        return payload or None

    async def head(self, url: str) -> bool:
        """Probe through the declared transport without allocating response bytes."""
        try:
            return (await self.network.head(url)).status == HTTP_OK
        except NetworkUnavailableError:
            logger.warning("Dukascopy source probe exhausted transport")
            return False


async def _fetch_m1_day_direct(
    network: NetworkAccess,
    symbol: str,
    dt_day: date,
    decimals: int,
    candle_type: str = "BID",
) -> Any:
    """Return the source's raw floating M1 frame through a declared transport."""
    instant = datetime.combine(dt_day, datetime.min.time(), tzinfo=UTC)
    if decimals != _symbol_decimals(symbol) or candle_type not in ("BID", "ASK"):
        raise ValueError("Invalid source scale/feed")
    url = _standard_url(_symbol(symbol), instant, "m1").replace(
        "BID_candles", candle_type + "_candles"
    )
    payload, _ = await _direct_payload(network, url, RateCorrector())
    raw = _decompress_bi5(payload)
    if not raw or len(raw) % M1_RECORD.size:
        return None
    rows = np.frombuffer(
        raw,
        dtype=np.dtype(
            [
                ("offset_sec", ">i4"),
                ("open", ">i4"),
                ("close", ">i4"),
                ("low", ">i4"),
                ("high", ">i4"),
                ("vol", ">f4"),
            ]
        ),
    )
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                int(instant.timestamp()) + rows["offset_sec"].astype(np.int64),
                unit="s",
                utc=True,
            ),
            **{
                key: np.round(rows[key] * 10.0**-decimals, decimals)
                for key in ("open", "high", "low", "close")
            },
            "volume": np.round(rows["vol"] * 1e6, 2),
        }
    )
    logger.info("Dukascopy direct frame: rows=%d", len(frame))
    return frame


async def _fetch_tick_hour_direct(
    network: NetworkAccess, symbol: str, dt_hour: datetime, decimals: int
) -> tuple[Any, Any, Any, Any, Any] | None:
    """Return source timestamps/prices and lossless per-side provider volumes."""
    if decimals != _symbol_decimals(symbol):
        raise ValueError("Invalid source scale")
    instant = _parse_datetime(dt_hour)
    payload, _ = await _direct_payload(
        network,
        _standard_url(_symbol(symbol), instant, "ticks", instant.hour),
        RateCorrector(),
    )
    raw = _decompress_bi5(payload)
    if not raw or len(raw) % TICK_RECORD.size:
        return None
    rows = np.frombuffer(
        raw,
        dtype=np.dtype(
            [
                ("offset_ms", ">i4"),
                ("ask", ">i4"),
                ("bid", ">i4"),
                ("ask_vol", ">f4"),
                ("bid_vol", ">f4"),
            ]
        ),
    )
    logger.info("Dukascopy direct tick arrays: rows=%d", len(rows))
    return (
        (
            int(instant.replace(minute=0, second=0, microsecond=0).timestamp() * 1000)
            + rows["offset_ms"].astype(np.int64)
        ),
        np.round(rows["ask"] * 10.0**-decimals, decimals),
        np.round(rows["bid"] * 10.0**-decimals, decimals),
        np.round(rows["ask_vol"] * 1e6, 2),
        np.round(rows["bid_vol"] * 1e6, 2),
    )


def _dataframe_to_canonical_m1(frame: Any) -> Any:
    """Convert source float OHLC/volume columns into the shared canonical schema."""
    # Explicit unit conversion also supports pandas 3's microsecond resolution.
    stamps = [
        int(value.timestamp() * 1000)
        for value in pd.to_datetime(frame["timestamp"], utc=True)
    ]
    volumes = np.round(frame["volume"].to_numpy()).astype(np.uint64)
    logger.info("Dukascopy canonical M1 conversion: rows=%d", len(frame))
    return _arrow_rows(
        [
            (
                stamp,
                float(row.open),
                float(row.high),
                float(row.low),
                float(row.close),
                int(volume),
            )
            for stamp, row, volume in zip(
                stamps, frame.itertuples(), volumes, strict=True
            )
        ],
        "m1",
    )


def _dataframe_to_canonical_ticks(frame: Any) -> Any:
    """Combine source side volumes and fixed-point prices exactly once."""
    stamps = [
        int(value.timestamp() * 1000)
        for value in pd.to_datetime(frame["timestamp"], utc=True)
    ]
    volumes = (
        frame["volume"].to_numpy()
        if "volume" in frame
        else frame["ask_volume"].to_numpy() + frame["bid_volume"].to_numpy()
    )
    asks = np.round(frame["ask"].to_numpy() * 1_000_000).astype(np.int64)
    bids = np.round(frame["bid"].to_numpy() * 1_000_000).astype(np.int64)
    logger.info("Dukascopy canonical tick conversion: rows=%d", len(frame))
    return _arrow_rows(
        [
            (stamp, int(ask), int(bid), int(volume))
            for stamp, ask, bid, volume in zip(
                stamps, asks, bids, np.round(volumes).astype(np.uint64), strict=True
            )
        ],
        "ticks",
    )


def _scan_market(  # noqa: PLR0917 -- source scan adapter inputs.
    symbol: str,
    kind: str,
    start: str | date | datetime | None,
    end: str | date | datetime | None,
    store_root: str | Path,
    source: str,
    tz: str | None,
    client: Client | None,
) -> Any:
    connection = _client(client)
    _validate_custody(connection, source, store_root)
    matches = [
        row
        for row in _dashboard(symbol=_symbol(symbol), client=connection)
        if row["timeframe"] == ("M1" if kind == "m1" else "TICK")
    ]
    if not matches:
        logger.info("Dukascopy scan has no matching definition")
        return pd.DataFrame()
    if len(matches) != 1:
        raise ClientError("Choose an unambiguous source definition")
    frames = list(
        _row_frames(
            connection,
            matches[0]["id"],
            start or "1900-01-01",
            end or datetime.now(UTC),
            tz=tz,
        )
    )
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _resample(frame: Any, timeframe: str, *, lower: bool = False) -> Any:
    timeframe = timeframe.lower().strip()
    if frame.empty or timeframe == "m1":
        return frame
    stamp = "timestamp" if lower else "DateTime"
    columns = (
        ("open", "high", "low", "close", "volume")
        if lower
        else ("Open", "High", "Low", "Close", "Volume")
    )
    frequencies = {
        "m5": "5min",
        "m15": "15min",
        "m30": "30min",
        "h1": "1h",
        "h4": "4h",
        "d1": "1D",
        "w1": "1W",
    }
    logger.info("Dukascopy resampling: timeframe=%s", timeframe)
    if not lower:
        # The reference's installed Polars scan labels weekly bins at Monday
        # midnight. Its download-candles API separately uses pandas resampling.
        frequency = {
            "m5": "5m",
            "m15": "15m",
            "m30": "30m",
            "h1": "1h",
            "h4": "4h",
            "d1": "1d",
            "w1": "1w",
        }.get(timeframe, timeframe)
        return (
            pl.from_pandas(frame)
            .sort(stamp)
            .group_by_dynamic(stamp, every=frequency)
            .agg(
                [
                    pl.col(columns[0]).first(),
                    pl.col(columns[1]).max(),
                    pl.col(columns[2]).min(),
                    pl.col(columns[3]).last(),
                    pl.col(columns[4]).sum(),
                ]
            )
            .to_pandas()
        )
    return (
        frame.set_index(stamp)
        .resample(frequencies.get(timeframe.lower(), timeframe))
        .agg(dict(zip(columns, ("first", "max", "min", "last", "sum"), strict=True)))
        .dropna()
        .reset_index()
    )


def _scan_market_m1(  # noqa: PLR0917 -- reference public signature.
    symbol: str,
    timeframe: str = "m1",
    start: str | date | datetime | None = None,
    end: str | date | datetime | None = None,
    store_root: str | Path = "data/market",
    source: str = "dukascopy",
    tz: str | None = None,
    *,
    client: Client | None = None,
) -> Any:
    """Read canonical host rows and resample only the requested returned view."""
    frame = _resample(
        _scan_market(symbol, "m1", start, end, store_root, source, None, client),
        timeframe,
    )
    if tz and not frame.empty:
        frame["DateTime"] = frame["DateTime"].dt.tz_convert(tz)
    return frame


def _scan_market_ticks(  # noqa: PLR0917 -- reference public signature.
    symbol: str,
    start: str | date | datetime | None = None,
    end: str | date | datetime | None = None,
    store_root: str | Path = "data/market",
    source: str = "dukascopy",
    as_unscaled_floats: bool = False,
    tz: str | None = None,
    *,
    client: Client | None = None,
) -> Any:
    """Read canonical combined-volume ticks with optional price unscaling."""
    frame = _scan_market(symbol, "ticks", start, end, store_root, source, tz, client)
    if as_unscaled_floats and not frame.empty:
        frame["Ask"] = frame["Ask"] / 1_000_000
        frame["Bid"] = frame["Bid"] / 1_000_000
    return frame


def _download_m1(
    symbol: str,
    start: str | date | datetime,
    end: str | date | datetime,
    *,
    client: Client | None = None,
    workers: int = 4,
    use_cdn: bool = True,
    cdn_server: str = "SQX",
    show_progress: bool = True,
    store: str | Path | bool = "data/market",
    source: str = "dukascopy",
    mode: str = "missing",
    candle_type: str = "BID",
    tz: str | None = None,
    ignore_weekends: bool = True,
) -> Any:
    """Expose source M1 acquisition through the shared host job implementation."""
    return download_data(
        symbol,
        start,
        end,
        mode,
        source,
        cdn_server if use_cdn else "STANDARD",
        "M1",
        client=client,
        workers=workers,
        store=store,
        show_progress=show_progress,
        ignore_weekends=ignore_weekends,
        tz=tz,
        candle_type=candle_type,
    )[_symbol(symbol) + "_M1"]


def _download_ticks(
    symbol: str,
    start: str | date | datetime,
    end: str | date | datetime,
    *,
    client: Client | None = None,
    workers: int = 4,
    use_cdn: bool = True,
    cdn_server: str = "SQX",
    show_progress: bool = True,
    store: str | Path | bool = "data/market",
    source: str = "dukascopy",
    mode: str = "missing",
    tz: str | None = None,
    ignore_weekends: bool = True,
) -> Any:
    """Expose source tick acquisition through the shared host job implementation."""
    return download_data(
        symbol,
        start,
        end,
        mode,
        source,
        cdn_server if use_cdn else "STANDARD",
        "TICKS",
        client=client,
        workers=workers,
        store=store,
        show_progress=show_progress,
        ignore_weekends=ignore_weekends,
        tz=tz,
    )[_symbol(symbol) + "_TICKS"]


def _download_candles(
    symbol: str,
    timeframe: str = "m1",
    *,
    start: str | date | datetime,
    end: str | date | datetime,
    client: Client | None = None,
    **options: Any,
) -> Any:
    """Resample source M1 results without persisting derived timeframes."""
    return _resample(
        _download_m1(symbol, start, end, client=client, **options),
        timeframe,
        lower=True,
    )


async def _try_download_cdn_package(  # noqa: PLR0917 -- source package adapter inputs.
    network: NetworkAccess,
    symbol: str,
    year: int,
    month: int | None = None,
    cdn_server: str = "SQX",
    kind: str = "m1",
    *,
    archive_network: SourceNetwork,
) -> list[tuple[str, bytes]] | None:
    """Read bounded original-named ZIP members through declared host custody."""
    mode: Literal["cdn", "cdn-cn"] = (
        "cdn-cn" if cdn_server.upper() == "CHINA" else "cdn"
    )
    periods = [str(year)] if month is None else [f"{year}_{month:02d}", str(year)]
    del network  # Transport custody is explicitly the supplied archive session.
    for period in periods:
        url = _cdn_archive_url(
            mode,
            "ticks" if kind in ("tick", "ticks") else "m1",
            _symbol(symbol),
            period,
        )
        try:
            if (await archive_network.head(url)).status != HTTP_OK:
                continue
            async with archive_network.archive(url) as archive:
                members: list[tuple[str, bytes]] = []
                size = 0
                for name in archive.members():
                    data = archive.read(name)
                    size += len(data)
                    if size > MAX_DECOMPRESSED:
                        raise ValueError("CDN package exceeds return bounds")
                    members.append((name, data))
                logger.info("Dukascopy source CDN package: members=%d", len(members))
                return members
        except httpx.HTTPError, NetworkUnavailableError, zipfile.BadZipFile:
            logger.warning("Dukascopy source CDN package unavailable: %s", url)
    return None


def _resolve_market_partition_path(
    market: MarketAccess, symbol: str, kind: str, period: str, source: str = "dukascopy"
) -> Path:
    """Describe a canonical partition through host custody, without path discovery."""
    if source != "dukascopy":
        raise PermissionError("Peer source path access denied")
    return Path(market.market_path(kind, _symbol(symbol).lower(), period))


def _store_canonical_partitions(
    data: Any,
    symbol: str,
    kind: str = "m1",
    source: str = "dukascopy",
    *,
    market: MarketAccess,
) -> list[Path]:
    """Split source canonical rows into host-owned periods and merge timestamps."""
    if source != "dukascopy" or kind not in ("m1", "ticks"):
        raise PermissionError("Peer source publication denied")
    table = (
        data
        if isinstance(data, pa.Table)
        else _dataframe_to_canonical_ticks(data)
        if kind == "ticks"
        else _dataframe_to_canonical_m1(data)
    )
    partitions: dict[str, list[dict[str, Any]]] = {}
    for row in table.to_pylist():
        instant = row["DateTime"]
        period = (
            f"{instant.year:04d}"
            if kind == "m1"
            else f"{instant.year:04d}-{instant.month:02d}"
        )
        partitions.setdefault(period, []).append(row)
    result = []
    for period, rows in sorted(partitions.items()):
        rows.sort(key=lambda row: row["DateTime"])
        canonical = pa.Table.from_pylist(
            rows, schema=TICK_SCHEMA if kind == "ticks" else M1_SCHEMA
        )
        first = int(rows[0]["DateTime"].timestamp() * 1000)
        last = int(rows[-1]["DateTime"].timestamp() * 1000)
        market.replace_interval(
            kind=kind,
            symbol=_symbol(symbol).lower(),
            period=period,
            incoming=canonical,
            start_ms=first,
            end_ms=last,
            mode="standard",
            merge_timestamps=True,
        )
        result.append(_resolve_market_partition_path(market, symbol, kind, period))
    logger.info("Dukascopy source publication: partitions=%d", len(result))
    return result


def _update_market_catalog(
    symbol: str,
    kind: str = "m1",
    source: str = "dukascopy",
    *,
    client: Client | None = None,
) -> None:
    """Verify the catalog committed by host publication, avoiding second SQL truth."""
    rows = _dashboard(source, _symbol(symbol), client=client)
    logger.info("Dukascopy catalog verified: kind=%s definitions=%d", kind, len(rows))


def _get_existing_m1_dates(
    store_root: str | Path,
    source: str,
    symbol: str,
    years: list[int],
    *,
    client: Client | None = None,
) -> set[date]:
    """Return observed UTC sample dates using verified host reads."""
    if not years:
        return set()
    frame = _scan_market_m1(
        symbol,
        start=f"{min(years):04d}-01-01",
        end=f"{max(years):04d}-12-31",
        store_root=store_root,
        source=source,
        client=client,
    )
    logger.info("Dukascopy existing M1 dates inspected")
    return set(frame["DateTime"].dt.date) if not frame.empty else set()


def _get_existing_tick_hours(
    store_root: str | Path,
    source: str,
    symbol: str,
    year_months: list[tuple[int, int]],
    *,
    client: Client | None = None,
) -> set[datetime]:
    """Return observed UTC sample hours using verified host reads."""
    if not year_months:
        return set()
    first_year, first_month = min(year_months)
    last_year, last_month = max(year_months)
    end = (date(last_year, last_month, 28) + timedelta(days=4)).replace(
        day=1
    ) - timedelta(days=1)
    frame = _scan_market_ticks(
        symbol,
        start=date(first_year, first_month, 1),
        end=end,
        store_root=store_root,
        source=source,
        client=client,
    )
    logger.info("Dukascopy existing tick hours inspected")
    return (
        set(frame["DateTime"].dt.floor("h").dt.to_pydatetime())
        if not frame.empty
        else set()
    )


# Host discovery requires this lifecycle hook; it is not a user API export.
prepare = _prepare


if __name__ == "__main__":
    configure_boot_logging()
    try:
        raise SystemExit(_main())
    finally:
        close_host_logging()
