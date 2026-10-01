# ruff: noqa: INP001, PLR2004 -- source namespace and binary protocol constants
"""Darwinex source decoding and acquisition under host lifecycle.

Description:
    Preserves owner-script DAT decoding and bid/ask log synchronization, with
    explicit network, jobs and immutable storage instead of standalone globals.
Purpose:
    FEAT-DM-DARWINEX_ACQUISITION: Historical Darwinex source for Data Manager.
Key Capabilities:
    - FR-DARWINEX-DECODE: Source binary and log formats; logs decoded rows.
    - FR-DARWINEX-ACQUIRE: Source archive selection; logs acquisition progress.
    - FR-DARWINEX-PUBLISH: Host-owned partitions; logs actual publication.
Python API Usage:
    contribution = await prepare(capabilities)
    catalog = await contribution.invoke("catalog", {})
CLI Usage:
    uv run pytest tests/plugin/DataSource/test_darwinex.py --no-cov
"""

from __future__ import annotations

import asyncio
import base64
import dataclasses
import gzip
import io
import struct
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal, cast

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
from app.host.capabilities import HostCapabilities, JobAccess, MarketAccess
from app.host.contracts import Document
from app.host.jobs import Budget
from app.host.logging import get_logger
from app.host.network import SourceNetwork
from app.host.packages import PreparedContribution
from pydantic import Field, JsonValue, model_validator

logger = get_logger(__name__)
PLUGIN = {
    "id": "plugin.data_manager.darwinex",
    "kind": "plugin",
    "version": "1.0.0",
    "compatibility": "1",
    "owner_workspace_id": "workspace.data_manager",
    "slot_id": "data_source.acquisition",
    "contract_version": "1.0.0",
    "requires": [
        {"id": "host.market_data", "version": "1.0.0"},
        {"id": "host.jobs", "version": "1.0.0"},
        {"id": "host.network", "version": "1.0.0"},
    ],
}


TICK_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
        pa.field("Ask", pa.int64(), nullable=False),
        pa.field("Bid", pa.int64(), nullable=False),
        pa.field("Volume", pa.uint64(), nullable=False),
    ]
)

M1_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
        pa.field("Open", pa.float64(), nullable=False),
        pa.field("High", pa.float64(), nullable=False),
        pa.field("Low", pa.float64(), nullable=False),
        pa.field("Close", pa.float64(), nullable=False),
        pa.field("Volume", pa.uint64(), nullable=False),
    ]
)

CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/darwinex"

CDN_HK_URL = "https://cdn005.strategyquantcdn.com/data/darwinex"

VOLUME_CONSTANT = 100000.0

EMBEDDED_DARWINEX_CSV = """AUDCAD;01.10.2017;5;75000;3;0.0001;0.00001;3
AUDCHF;01.10.2017;5;100000;4;0.0001;0.00001;3
AUDJPY;01.10.2017;3;900;3;0.01;0.001;3
AUDNZD;01.10.2017;5;68000;5;0.0001;0.00001;3
AUDUSD;01.10.2017;5;100000;3;0.0001;0.00001;3
AUS200;01.10.2017;3;25;3;1;1;6
CADCHF;01.10.2017;5;100000;5;0.0001;0.00001;3
CADJPY;01.10.2017;3;900;3;0.01;0.001;3
CHFJPY;01.10.2017;3;900;3;0.01;0.001;3
EURAUD;01.10.2017;5;73000;4;0.0001;0.00001;3
EURCAD;01.10.2017;5;75000;3;0.0001;0.00001;3
EURCHF;01.10.2017;5;100000;4;0.0001;0.00001;3
EURGBP;01.10.2017;5;132000;4;0.0001;0.00001;3
EURJPY;01.10.2017;3;900;3;0.01;0.001;3
EURMXN;01.10.2017;5;5300;30;0.01;0.001;3
EURNOK;01.10.2017;5;12200;36;0.0001;0.00001;3
EURNZD;01.10.2017;5;68000;4;0.0001;0.00001;3
EURSGD;14.10.2018;5;73000;41;0.0001;0.00001;3
EURTRY;01.10.2017;5;21000;45;0.0001;0.00001;3
EURUSD;01.10.2017;5;100000;3;0.0001;0.00001;3
FCHI;27.06.2018;3;12;3;1;0.1;6
GBPAUD;01.10.2017;5;73000;8;0.0001;0.00001;3
GBPCAD;01.10.2017;5;75000;8;0.0001;0.00001;3
GBPCHF;01.10.2017;5;100000;8;0.0001;0.00001;3
GBPJPY;01.10.2017;3;900;5;0.01;0.001;3
GBPMXN;01.10.2017;3;5300;5;0.00001;0.00001;3
GBPNOK;01.10.2017;5;11800;12;0.0001;0.00001;3
GBPNZD;01.10.2017;5;68000;12;0.0001;0.00001;3
GBPTRY;01.10.2017;5;17200;120;0.0001;0.00001;3
GBPUSD;01.10.2017;5;100000;3;0.0001;0.00001;3
GDAXIm;27.06.2018;3;30;3;1;0.1;6
NI225;01.10.2017;3;10;10;1;0.1;6
NDXm;27.06.2018;3;12;12;1;0.1;6
NZDCAD;01.10.2017;5;75000;5;0.0001;0.00001;3
NZDCHF;01.10.2017;5;100000;5;0.0001;0.00001;3
NZDJPY;01.10.2017;3;900;4;0.01;0.001;3
NZDUSD;01.10.2017;5;100000;4;0.0001;0.00001;3
SPN35;27.06.2018;3;12;4;1;0.1;6
SP500;27.06.2018;3;50;3;1;0.01;6
STOXX50E;01.10.2017;3;12;4;1;0.1;6
UK100;01.10.2017;3;12;3;1;0.1;6
USDCAD;01.10.2017;5;75000;3;0.0001;0.00001;3
USDCHF;01.10.2017;5;100000;3;0.0001;0.00001;3
USDHKD;19.2.2018;5;12500;30;0.0001;0.00001;3
USDJPY;01.10.2017;3;900;3;0.01;0.001;3
USDMXN;01.10.2017;5;5300;250;0.0001;0.00001;3
USDNOK;01.10.2017;5;12000;120;0.0001;0.00001;3
USDSEK;01.10.2017;5;11200;60;0.0001;0.00001;3
USDSGD;01.10.2017;5;73000;10;0.0001;0.00001;3
USDTRY;01.10.2017;5;21000;90;0.0001;0.00001;3
WS30;01.10.2017;3;5;3;1;0.01;6
XAGUSD;01.10.2017;3;5000;60;0.01;0.001;3
XAUUSD;01.10.2017;3;100;60;0.01;0.01;3
XBNUSD;27.06.2018;3;100;8;0.0001;0.00001;7
XBTUSD;27.06.2018;3;100;150;0.001;0.001;7
XETUSD;27.06.2018;3;100;150;0.0001;0.00001;7
XLCUSD;27.06.2018;3;100;150;0.0001;0.00001;7
XNGUSD;01.10.2017;3;0.1;150;0.0001;0.0001;4
XPDUSD;01.10.2017;3;100;150;0.0001;0.00001;3
XPTUSD;01.10.2017;3;100;500;0.01;0.001;4
XRPUSD;27.06.2018;3;100;150;0.01;0.01;7
XTIUSD;01.10.2017;3;1000;6;0.01;0.01;4
AAL;02.12.2019;3;1;0;0.01;0.01;1
AAPL;02.12.2019;3;1;0;0.01;0.01;1
ABBV;02.12.2019;3;1;0;0.01;0.01;1
ABMD;02.12.2019;3;1;0;0.01;0.01;1
ABT;02.12.2019;3;1;0;0.01;0.01;1
ACN;13.4.2020;3;1;0;0.01;0.01;1
ADBE;02.12.2019;3;1;0;0.01;0.01;1
ADI;02.12.2019;3;1;0;0.01;0.01;1
ADM;02.12.2019;3;1;0;0.01;0.01;1
ADP;02.12.2019;3;1;0;0.01;0.01;1
ADSK;02.12.2019;3;1;0;0.01;0.01;1
AEP;02.12.2019;3;1;0;0.01;0.01;1
AGN;02.12.2019;3;1;0;0.01;0.01;1
AIG;02.12.2019;3;1;0;0.01;0.01;1
ALGN;02.12.2019;3;1;0;0.01;0.01;1
ALL;02.12.2019;3;1;0;0.01;0.01;1
ALXN;02.12.2019;3;1;0;0.01;0.01;1
AMAT;02.12.2019;3;1;0;0.01;0.01;1
AMD;14.03.2020;3;1;0;0.01;0.01;1
AMGN;02.12.2019;3;1;0;0.01;0.01;1
AMT;02.12.2019;3;1;0;0.01;0.01;1
AMZN;02.12.2019;3;1;0;0.01;0.01;1
ANET;02.12.2019;3;1;0;0.01;0.01;1
ANTM;02.12.2019;3;1;0;0.01;0.01;1
APD;02.12.2019;3;1;0;0.01;0.01;1
ATVI;02.12.2019;3;1;0;0.01;0.01;1
AVGO;02.12.2019;3;1;0;0.01;0.01;1
AXP;02.12.2019;3;1;0;0.01;0.01;1
AZO;02.12.2019;3;1;0;0.01;0.01;1
BA;02.12.2019;3;1;0;0.01;0.01;1
BAC;02.12.2019;3;1;0;0.01;0.01;1
BAX;02.12.2019;3;1;0;0.01;0.01;1
BBT;02.12.2019;3;1;0;0.01;0.01;1
BBY;02.12.2019;3;1;0;0.01;0.01;1
BDX;02.12.2019;3;1;0;0.01;0.01;1
BIIB;02.12.2019;3;1;0;0.01;0.01;1
BK;02.12.2019;3;1;0;0.01;0.01;1
BKNG;02.12.2019;3;1;0;0.01;0.01;1
BLK;02.12.2019;3;1;0;0.01;0.01;1
BMY;02.12.2019;3;1;0;0.01;0.01;1
BRKb;13.04.2020;3;1;0;0.01;0.01;1
BSX;02.12.2019;3;1;0;0.01;0.01;1
C;02.12.2019;3;1;0;0.01;0.01;1
CAH;02.12.2019;3;1;0;0.01;0.01;1
CAT;02.12.2019;3;1;0;0.01;0.01;1
CB;13.04.2020;3;1;0;0.01;0.01;1
CBS;02.12.2019;3;1;0;0.01;0.01;1
CCI;02.12.2019;3;1;0;0.01;0.01;1
CCL;02.12.2019;3;1;0;0.01;0.01;1
CHTR;02.12.2019;3;1;0;0.01;0.01;1
CI;02.12.2019;3;1;0;0.01;0.01;1
CL;02.12.2019;3;1;0;0.01;0.01;1
CLX;02.12.2019;3;1;0;0.01;0.01;1
CMA;02.12.2019;3;1;0;0.01;0.01;1
CMCSA;02.12.2019;3;1;0;0.01;0.01;1
CME;02.12.2019;3;1;0;0.01;0.01;1
CMI;02.12.2019;3;1;0;0.01;0.01;1
CNC;02.12.2019;3;1;0;0.01;0.01;1
COF;02.12.2019;3;1;0;0.01;0.01;1
COP;02.12.2019;3;1;0;0.01;0.01;1
COST;02.12.2019;3;1;0;0.01;0.01;1
CRM;02.12.2019;3;1;0;0.01;0.01;1
CSCO;02.12.2019;3;1;0;0.01;0.01;1
CSX;02.12.2019;3;1;0;0.01;0.01;1
CTL;02.12.2019;3;1;0;0.01;0.01;1
CTSH;02.12.2019;3;1;0;0.01;0.01;1
CVS;02.12.2019;3;1;0;0.01;0.01;1
CVX;02.12.2019;3;1;0;0.01;0.01;1
CXO;02.12.2019;3;1;0;0.01;0.01;1
D;02.12.2019;3;1;0;0.01;0.01;1
DAL;02.12.2019;3;1;0;0.01;0.01;1
DD;13.04.2020;3;1;0;0.01;0.01;1
DE;02.12.2019;3;1;0;0.01;0.01;1
DFS;02.12.2019;3;1;0;0.01;0.01;1
DG;02.12.2019;3;1;0;0.01;0.01;1
DHI;02.12.2019;3;1;0;0.01;0.01;1
DHR;02.12.2019;3;1;0;0.01;0.01;1
DIS;02.12.2019;3;1;0;0.01;0.01;1
DLTR;02.12.2019;3;1;0;0.01;0.01;1
DOW;02.12.2019;3;1;0;0.01;0.01;1
DUK;02.12.2019;3;1;0;0.01;0.01;1
DVN;02.12.2019;3;1;0;0.01;0.01;1
DXC;02.12.2019;3;1;0;0.01;0.01;1
EA;02.12.2019;3;1;0;0.01;0.01;1
EBAY;02.12.2019;3;1;0;0.01;0.01;1
EL;02.12.2019;3;1;0;0.01;0.01;1
EMR;02.12.2019;3;1;0;0.01;0.01;1
EOG;02.12.2019;3;1;0;0.01;0.01;1
EQIX;02.12.2019;3;1;0;0.01;0.01;1
ETN;02.12.2019;3;1;0;0.01;0.01;1
EURSEK;02.12.2019;5;11200;35;0.0001;0.00001;3
EW;02.12.2019;3;1;0;0.01;0.01;1
EXC;02.12.2019;3;1;0;0.01;0.01;1
EXPE;02.12.2019;3;1;0;0.01;0.01;1
FAST;02.12.2019;3;1;0;0.01;0.01;1
FB;02.12.2019;3;1;0;0.01;0.01;1
FCX;02.12.2019;3;1;0;0.01;0.01;1
FDX;02.12.2019;3;1;0;0.01;0.01;1
FIS;13.04.2020;3;1;0;0.01;0.01;1
FISV;13.04.2020;3;1;0;0.01;0.01;1
FITB;02.12.2019;3;1;0;0.01;0.01;1
FOX;02.12.2019;3;1;0;0.01;0.01;1
FOXA;02.12.2019;3;1;0;0.01;0.01;1
FTV;02.12.2019;3;1;0;0.01;0.01;1
G30mic;02.12.2019;3;27;3;1;0.1;6
GBPSEK;02.12.2019;3;27;3;1;0.1;6
GBPSGD;02.12.2019;3;27;3;1;0.1;6
GD;02.12.2019;3;1;0;0.01;0.01;1
GE;02.12.2019;3;1;0;0.01;0.01;1
GILD;02.12.2019;3;1;0;0.01;0.01;1
GIS;02.12.2019;3;1;0;0.01;0.01;1
GLW;02.12.2019;3;1;0;0.01;0.01;1
GM;02.12.2019;3;1;0;0.01;0.01;1
GOOG;02.12.2019;3;1;0;0.01;0.01;1
GOOGL;02.12.2019;3;1;0;0.01;0.01;1
GS;02.12.2019;3;1;0;0.01;0.01;1
GWW;02.12.2019;3;1;0;0.01;0.01;1
HAL;02.12.2019;3;1;0;0.01;0.01;1
HCA;02.12.2019;3;1;0;0.01;0.01;1
HD;02.12.2019;3;1;0;0.01;0.01;1
HES;02.12.2019;3;1;0;0.01;0.01;1
HLT;02.12.2019;3;1;0;0.01;0.01;1
HON;02.12.2019;3;1;0;0.01;0.01;1
HPE;02.12.2019;3;1;0;0.01;0.01;1
HPQ;02.12.2019;3;1;0;0.01;0.01;1
HUM;02.12.2019;3;1;0;0.01;0.01;1
IAC;02.12.2019;3;1;0;0.01;0.01;1
IBM;02.12.2019;3;1;0;0.01;0.01;1
ICE;02.12.2019;3;1;0;0.01;0.01;1
ILMN;02.12.2019;3;1;0;0.01;0.01;1
INTC;02.12.2019;3;1;0;0.01;0.01;1
INTU;02.12.2019;3;1;0;0.01;0.01;1
IQV;02.12.2019;3;1;0;0.01;0.01;1
ISRG;02.12.2019;3;1;0;0.01;0.01;1
ITW;02.12.2019;3;1;0;0.01;0.01;1
JCI;02.12.2019;3;1;0;0.01;0.01;1
JNJ;02.12.2019;3;1;0;0.01;0.01;1
JPM;02.12.2019;3;1;0;0.01;0.01;1
KDP;02.12.2019;3;1;0;0.01;0.01;1
KEY;02.12.2019;3;1;0;0.01;0.01;1
KHC;02.12.2019;3;1;0;0.01;0.01;1
KLAC;02.12.2019;3;1;0;0.01;0.01;1
KMB;02.12.2019;3;1;0;0.01;0.01;1
KMI;02.12.2019;3;1;0;0.01;0.01;1
KO;02.12.2019;3;1;0;0.01;0.01;1
KR;02.12.2019;3;1;0;0.01;0.01;1
LEN;02.12.2019;3;1;0;0.01;0.01;1
LLY;02.12.2019;3;1;0;0.01;0.01;1
LMT;02.12.2019;3;1;0;0.01;0.01;1
LOW;02.12.2019;3;1;0;0.01;0.01;1
LRCX;02.12.2019;3;1;0;0.01;0.01;1
LUV;02.12.2019;3;1;0;0.01;0.01;1
LVS;02.12.2019;3;1;0;0.01;0.01;1
LYB;02.12.2019;3;1;0;0.01;0.01;1
MA;02.12.2019;3;1;0;0.01;0.01;1
MAR;02.12.2019;3;1;0;0.01;0.01;1
MCD;02.12.2019;3;1;0;0.01;0.01;1
MCHP;02.12.2019;3;1;0;0.01;0.01;1
MCK;02.12.2019;3;1;0;0.01;0.01;1
MDLZ;02.12.2019;3;1;0;0.01;0.01;1
MDT;13.04.2020;3;1;0;0.01;0.01;1
MET;02.12.2019;3;1;0;0.01;0.01;1
MMC;02.12.2019;3;1;0;0.01;0.01;1
MMM;02.12.2019;3;1;0;0.01;0.01;1
MO;02.12.2019;3;1;0;0.01;0.01;1
MPC;02.12.2019;3;1;0;0.01;0.01;1
MRK;02.12.2019;3;1;0;0.01;0.01;1
MRO;02.12.2019;3;1;0;0.01;0.01;1
MS;02.12.2019;3;1;0;0.01;0.01;1
MSFT;02.12.2019;3;1;0;0.01;0.01;1
MTB;02.12.2019;3;1;0;0.01;0.01;1
MU;02.12.2019;3;1;0;0.01;0.01;1
NEE;02.12.2019;3;1;0;0.01;0.01;1
NEM;02.12.2019;3;1;0;0.01;0.01;1
NFLX;02.12.2019;3;1;0;0.01;0.01;1
NKE;02.12.2019;3;1;0;0.01;0.01;1
NOC;02.12.2019;3;1;0;0.01;0.01;1
NOW;02.12.2019;3;1;0;0.01;0.01;1
NSC;02.12.2019;3;1;0;0.01;0.01;1
NTAP;02.12.2019;3;1;0;0.01;0.01;1
NVDA;02.12.2019;3;1;0;0.01;0.01;1
OKE;02.12.2019;3;1;0;0.01;0.01;1
OMC;02.12.2019;3;1;0;0.01;0.01;1
ORCL;02.12.2019;3;1;0;0.01;0.01;1
ORLY;02.12.2019;3;1;0;0.01;0.01;1
OXY;02.12.2019;3;1;0;0.01;0.01;1
PANW;02.12.2019;3;1;0;0.01;0.01;1
PCG;02.12.2019;3;1;0;0.01;0.01;1
PEP;02.12.2019;3;1;0;0.01;0.01;1
PFE;02.12.2019;3;1;0;0.01;0.01;1
PG;02.12.2019;3;1;0;0.01;0.01;1
PGR;02.12.2019;3;1;0;0.01;0.01;1
PH;02.12.2019;3;1;0;0.01;0.01;1
PLD;02.12.2019;3;1;0;0.01;0.01;1
PM;02.12.2019;3;1;0;0.01;0.01;1
PNC;02.12.2019;3;1;0;0.01;0.01;1
PPG;02.12.2019;3;1;0;0.01;0.01;1
PRU;02.12.2019;3;1;0;0.01;0.01;1
PSA;02.12.2019;3;1;0;0.01;0.01;1
PSX;18.02.2018;3;1;0;0.01;0.01;1
PXD;02.12.2019;3;1;0;0.01;0.01;1
PYPL;02.12.2019;3;1;0;0.01;0.01;1
QCOM;02.12.2019;3;1;0;0.01;0.01;1
RCL;02.12.2019;3;1;0;0.01;0.01;1
REGN;02.12.2019;3;1;0;0.01;0.01;1
RF;02.12.2019;3;1;0;0.01;0.01;1
ROK;02.12.2019;3;1;0;0.01;0.01;1
ROST;02.12.2019;3;1;0;0.01;0.01;1
RTN;02.12.2019;3;1;0;0.01;0.01;1
SBUX;02.12.2019;3;1;0;0.01;0.01;1
SCHW;02.12.2019;3;1;0;0.01;0.01;1
SHW;02.12.2019;3;1;0;0.01;0.01;1
SLB;02.12.2019;3;1;0;0.01;0.01;1
SO;02.12.2019;3;1;0;0.01;0.01;1
SPG;02.12.2019;3;1;0;0.01;0.01;1
SPGI;02.12.2019;3;1;0;0.01;0.01;1
SPLK;02.12.2019;3;1;0;0.01;0.01;1
SRE;02.12.2019;3;1;0;0.01;0.01;1
STI;02.12.2019;3;1;0;0.01;0.01;1
STT;02.12.2019;3;1;0;0.01;0.01;1
STZ;02.12.2019;3;1;0;0.01;0.01;1
SWK;02.12.2019;3;1;0;0.01;0.01;1
SWKS;02.12.2019;3;1;0;0.01;0.01;1
SYF;02.12.2019;3;1;0;0.01;0.01;1
SYK;02.12.2019;3;1;0;0.01;0.01;1
SYY;02.12.2019;3;1;0;0.01;0.01;1
T;02.12.2019;3;1;0;0.01;0.01;1
TGT;02.12.2019;3;1;0;0.01;0.01;1
TIF;02.12.2019;3;1;0;0.01;0.01;1
TJX;02.12.2019;3;1;0;0.01;0.01;1
TMO;02.12.2019;3;1;0;0.01;0.01;1
TMUS;02.12.2019;3;1;0;0.01;0.01;1
TRV;02.12.2019;3;1;0;0.01;0.01;1
TSLA;02.12.2019;3;1;0;0.01;0.01;1
TSN;02.12.2019;3;1;0;0.01;0.01;1
TTWO;02.12.2019;3;1;0;0.01;0.01;1
TWTR;02.12.2019;3;1;0;0.01;0.01;1
TXN;02.12.2019;3;1;0;0.01;0.01;1
UAL;02.12.2019;3;1;0;0.01;0.01;1
ULTA;02.12.2019;3;1;0;0.01;0.01;1
UNH;02.12.2019;3;1;0;0.01;0.01;1
UNP;02.12.2019;3;1;0;0.01;0.01;1
UPS;02.12.2019;3;1;0;0.01;0.01;1
USB;02.12.2019;3;1;0;0.01;0.01;1
UTX;02.12.2019;3;1;0;0.01;0.01;1
V;02.12.2019;3;1;0;0.01;0.01;1
VFC;02.12.2019;3;1;0;0.01;0.01;1
VLO;02.12.2019;3;1;0;0.01;0.01;1
VMW;02.12.2019;3;1;0;0.01;0.01;1
VRTX;02.12.2019;3;1;0;0.01;0.01;1
VZ;02.12.2019;3;1;0;0.01;0.01;1
WBA;02.12.2019;3;1;0;0.01;0.01;1
WCG;02.12.2019;3;1;0;0.01;0.01;1
WDAY;02.12.2019;3;1;0;0.01;0.01;1
WDC;02.12.2019;3;1;0;0.01;0.01;1
WFC;02.12.2019;3;1;0;0.01;0.01;1
WM;02.12.2019;3;1;0;0.01;0.01;1
WMB;02.12.2019;3;1;0;0.01;0.01;1
WMT;02.12.2019;3;1;0;0.01;0.01;1
XLNX;02.12.2019;3;1;0;0.01;0.01;1
XOM;02.12.2019;3;1;0;0.01;0.01;1
ZTS;02.12.2019;3;1;0;0.01;0.01;1
ADAUSD;06.04.2025;4;1;30;0.001;0.0001;7
BTCUSD;06.04.2025;5;1;5;0.1;0.01;7
DOGEUSD;06.04.2025;5;1;30;0.0001;0.00001;7
SOLUSD;06.04.2025;3;1;20;0.01;0.001;7"""


class SQBinaryDatDecoder:
    """Preserve the owner script's numerical decoding behavior."""

    @staticmethod
    def decode(  # noqa: C901, PLR0912, PLR0915 -- source binary state machine.
        source: bytes | io.BytesIO,
        price_scaling: float = 1000000.0,  # noqa: ARG004 -- source parameter is unused.
        volume_constant: float = VOLUME_CONSTANT,  # noqa: ARG004 -- source parameter is unused.
    ) -> tuple[npt.NDArray[Any], npt.NDArray[Any], npt.NDArray[Any], npt.NDArray[Any]]:
        """Preserve the owner script's numerical decoding behavior."""
        stream = io.BytesIO(source) if isinstance(source, bytes) else source

        def read_utf() -> str:
            buf = stream.read(2)
            if len(buf) < 2:
                raise EOFError("Unexpected EOF reading UTF length")
            ln = struct.unpack(">H", buf)[0]
            str_bytes = stream.read(ln)
            return str_bytes.decode("utf-8", errors="replace")

        ver = read_utf()
        if ver not in ("4.1", "4.2"):
            raise ValueError(f"Unsupported StrategyQuant DAT version: {ver}")
        typ = read_utf()
        if typ not in ("D", "C"):
            raise ValueError(f"Unsupported StrategyQuant DAT file type: {typ}")
        _code = read_utf()
        buf_rec = stream.read(8)
        if len(buf_rec) < 8:
            return (
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.uint64),
            )
        total_records = struct.unpack(">q", buf_rec)[0]
        if total_records > 4_000_000:
            raise ValueError("DAT record count exceeds bounded decode limit")
        col_cnt_bytes = stream.read(4)
        col_cnt = struct.unpack(">i", col_cnt_bytes)[0]
        for _ in range(col_cnt):
            read_utf()
            stream.read(4)
        magic = read_utf()
        if magic != "SnRbTs":
            raise ValueError(
                f"Invalid DAT magic header: {magic}, file may be corrupted."
            )
        if typ == "C":
            mod_len = struct.unpack(">i", stream.read(4))[0]
            stream.read(mod_len)
        if total_records <= 0:
            return (
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.uint64),
            )
        chain = stream.read(15)
        if len(chain) == 15 and list(chain) == list(range(15)):
            stream.read(4)
        else:
            stream.seek(stream.tell() - len(chain))
        times = np.empty(total_records, dtype=np.int64)
        asks = np.empty(total_records, dtype=np.int64)
        bids = np.empty(total_records, dtype=np.int64)
        vols = np.empty(total_records, dtype=np.uint64)
        read_b = stream.read
        prev_time = 0
        prev_ask = 0
        prev_bid = 0
        prev_vol = 0
        for i in range(total_records):
            if i > 0 and i % 1000 == 0:
                ch = read_b(15)
                if len(ch) == 15 and list(ch) == list(range(15)):
                    read_b(4)
                else:
                    raise ValueError("DAT block marker is missing or corrupt")
            cfg = read_b(2)
            if len(cfg) < 2:
                times = times[:i]
                asks = asks[:i]
                bids = bids[:i]
                vols = vols[:i]
                break
            b0 = cfg[0]
            b1 = cfg[1]
            ask_dt = b0 & 3
            ask_logic = b0 >> 2 & 3
            time_dt = b0 >> 4 & 3
            time_logic = b0 >> 6 & 3
            vol_dt = b1 & 3
            vol_logic = b1 >> 2 & 3
            bid_dt = b1 >> 4 & 3
            bid_logic = b1 >> 6 & 3
            if time_dt == 0:
                val_t = read_b(1)[0]
            elif time_dt == 1:
                bb = read_b(2)
                val_t = bb[0] << 8 | bb[1]
            elif time_dt == 2:
                bb = read_b(4)
                val_t = bb[0] << 24 | bb[1] << 16 | bb[2] << 8 | bb[3]
            else:
                bb = read_b(8)
                val_t = struct.unpack(">Q", bb)[0]
            if time_logic == 0:
                prev_time -= val_t
            elif time_logic == 1:
                prev_time += val_t
            else:
                prev_time = val_t
            times[i] = prev_time
            if ask_dt == 0:
                val_a = read_b(1)[0]
            elif ask_dt == 1:
                bb = read_b(2)
                val_a = bb[0] << 8 | bb[1]
            elif ask_dt == 2:
                bb = read_b(4)
                val_a = bb[0] << 24 | bb[1] << 16 | bb[2] << 8 | bb[3]
            else:
                bb = read_b(8)
                val_a = struct.unpack(">Q", bb)[0]
            if ask_logic == 0:
                prev_ask -= val_a
            elif ask_logic == 1:
                prev_ask += val_a
            else:
                prev_ask = val_a
            asks[i] = prev_ask
            if bid_dt == 0:
                val_b = read_b(1)[0]
            elif bid_dt == 1:
                bb = read_b(2)
                val_b = bb[0] << 8 | bb[1]
            elif bid_dt == 2:
                bb = read_b(4)
                val_b = bb[0] << 24 | bb[1] << 16 | bb[2] << 8 | bb[3]
            else:
                bb = read_b(8)
                val_b = struct.unpack(">Q", bb)[0]
            if bid_logic == 0:
                prev_bid -= val_b
            elif bid_logic == 1:
                prev_bid += val_b
            else:
                prev_bid = val_b
            bids[i] = prev_bid
            if vol_dt == 0:
                val_v = read_b(1)[0]
            elif vol_dt == 1:
                bb = read_b(2)
                val_v = bb[0] << 8 | bb[1]
            elif vol_dt == 2:
                bb = read_b(4)
                val_v = bb[0] << 24 | bb[1] << 16 | bb[2] << 8 | bb[3]
            else:
                bb = read_b(8)
                val_v = struct.unpack(">Q", bb)[0]
            if vol_logic == 0:
                prev_vol -= val_v
            elif vol_logic == 1:
                prev_vol += val_v
            else:
                prev_vol = val_v
            vols[i] = max(0, prev_vol)
        return (times, asks, bids, vols)

    @classmethod
    def decode_to_dataframe(
        cls, source: bytes | io.BytesIO, price_scaling: float = 1000000.0
    ) -> pd.DataFrame:
        """Expose decoded fixed-point source columns without file access."""
        times, asks, bids, vols = cls.decode(source, price_scaling=price_scaling)
        if len(times) == 0:
            return pd.DataFrame(columns=["DateTime", "Ask", "Bid", "Volume"])
        return pd.DataFrame(
            {
                "DateTime": pd.to_datetime(times, unit="ms", utc=True),
                "Ask": asks,
                "Bid": bids,
                "Volume": vols,
            }
        )


class DarwinexFileImporter:
    """Preserve the owner script's numerical decoding behavior."""

    @staticmethod
    def parse_tick_log_file(payload: bytes) -> list[tuple[int, float, float]]:
        """Parse supplied logs with the script's timestamp and missing-volume rules."""
        if payload.startswith(b"\x1f\x8b"):
            with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:
                payload = stream.read(128 * 1024 * 1024 + 1)
        if len(payload) > 128 * 1024 * 1024:
            raise ValueError("Darwinex log expansion exceeds limit")
        rows = []
        ignored = 0
        for line in payload.decode("utf-8", errors="replace").splitlines():
            fields = line.strip().split(",")
            if not line.strip():
                continue
            if len(fields) < 2:
                ignored += 1
                continue
            try:
                rows.append(
                    (
                        int(fields[0].strip()[:13]),
                        float(fields[1].strip()),
                        float(fields[2].strip()) if len(fields) > 2 else 1.0,
                    )
                )
            except ValueError:
                ignored += 1
        logger.info("Darwinex log parsed: rows=%d ignored=%d", len(rows), ignored)
        return rows

    @classmethod
    def merge_ask_bid_files(
        cls,
        ask_file: bytes | None,
        bid_file: bytes | None,
        last_state: dict[str, float] | None = None,
    ) -> tuple[
        npt.NDArray[Any],
        npt.NDArray[Any],
        npt.NDArray[Any],
        npt.NDArray[Any],
        dict[str, float],
    ]:
        """Preserve the owner script's numerical decoding behavior."""
        state = last_state or {"last_ask": 0.0, "last_bid": 0.0, "last_vol": 0.0}
        ticks_map: dict[int, dict[str, float]] = {}
        if ask_file:
            for ts, price, _vol in cls.parse_tick_log_file(ask_file):
                entry = ticks_map.setdefault(ts, {"ask": 0.0, "bid": 0.0, "vol": 0.0})
                entry["ask"] = price
        if bid_file:
            for ts, price, vol in cls.parse_tick_log_file(bid_file):
                entry = ticks_map.setdefault(ts, {"ask": 0.0, "bid": 0.0, "vol": 0.0})
                entry["bid"] = price
                entry["vol"] = vol
        if not ticks_map:
            return (
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.uint64),
                state,
            )
        sorted_timestamps = sorted(ticks_map.keys())
        n = len(sorted_timestamps)
        times = np.empty(n, dtype=np.int64)
        asks = np.empty(n, dtype=np.int64)
        bids = np.empty(n, dtype=np.int64)
        vols = np.empty(n, dtype=np.uint64)
        last_ask = state["last_ask"]
        last_bid = state["last_bid"]
        last_vol = state["last_vol"]
        for idx, ts in enumerate(sorted_timestamps):
            rec = ticks_map[ts]
            ask = rec["ask"]
            bid = rec["bid"]
            vol = rec["vol"]
            if ask == 0.0:
                ask = last_ask
            if bid == 0.0:
                bid = last_bid
            if vol == 0.0:
                vol = last_vol
            last_ask = ask
            last_bid = bid
            last_vol = vol
            times[idx] = ts
            asks[idx] = round(ask * 1000000.0)
            bids[idx] = round(bid * 1000000.0)
            vols[idx] = round(vol * 100000.0)
        state["last_ask"] = last_ask
        state["last_bid"] = last_bid
        state["last_vol"] = last_vol
        return (times, asks, bids, vols, state)


def ticks_to_m1(  # noqa: PLR0917 -- source array contract.
    ts_ms: npt.NDArray[Any],
    asks_scaled: npt.NDArray[Any],
    bids_scaled: npt.NDArray[Any],
    vols: npt.NDArray[Any],
    decimals: int = 5,
    candle_type: str = "BID",
) -> pd.DataFrame:
    """Preserve the source transformation and archive selection rules."""
    if len(ts_ms) == 0:
        return pd.DataFrame(
            columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
        )
    scale_factor = 1.0 / 1000000.0
    prices = (
        asks_scaled if candle_type.upper() == "ASK" else bids_scaled
    ) * scale_factor
    minute_ts = ts_ms // 60000 * 60000
    unique_minutes, first_indices = np.unique(minute_ts, return_index=True)
    _, last_rev = np.unique(minute_ts[::-1], return_index=True)
    last_indices = len(minute_ts) - 1 - last_rev
    opens = np.round(prices[first_indices], decimals)
    closes = np.round(prices[last_indices], decimals)
    highs = np.round(np.maximum.reduceat(prices, first_indices), decimals)
    lows = np.round(np.minimum.reduceat(prices, first_indices), decimals)
    vol_sums = np.add.reduceat(vols, first_indices)
    df_m1 = pd.DataFrame(
        {
            "DateTime": pd.to_datetime(unique_minutes, unit="ms", utc=True),
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": np.round(vol_sums).astype(np.uint64),
        }
    )
    return df_m1  # noqa: RET504 -- source transform retained.


def resample_candles(df_m1: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Preserve the source transformation and archive selection rules."""
    if df_m1.empty:
        return df_m1
    tf_map = {
        "m1": "1min",
        "m5": "5min",
        "m15": "15min",
        "m30": "30min",
        "h1": "1h",
        "h2": "2h",
        "h4": "4h",
        "h8": "8h",
        "d1": "1D",
        "w1": "1W",
        "mn1": "1ME",
        "m": "1ME",
    }
    freq = tf_map.get(timeframe.lower(), timeframe)
    df_indexed = df_m1.set_index("DateTime")
    resampled = (
        df_indexed.resample(freq)
        .agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        .dropna()
        .reset_index()
    )
    return resampled  # noqa: RET504 -- source transform retained.


def dataframe_to_canonical_ticks(df: pd.DataFrame) -> pa.Table:
    """Preserve the source transformation and archive selection rules."""
    if pa is None:
        raise ImportError("pyarrow is required.")
    if df.empty:
        return pa.Table.from_batches([], schema=TICK_SCHEMA)
    dt_col = df["DateTime"] if "DateTime" in df.columns else df["timestamp"]
    dt_arr = pa.Array.from_pandas(
        pd.to_datetime(dt_col, utc=True), type=pa.timestamp("ms", tz="UTC")
    )
    ask_col = df["Ask"] if "Ask" in df.columns else df["ask"]
    bid_col = df["Bid"] if "Bid" in df.columns else df["bid"]
    vol_col = df["Volume"] if "Volume" in df.columns else df["volume"]
    if np.issubdtype(ask_col.dtype, np.floating):
        ask_scaled = np.round(ask_col.values * 1000000.0).astype(np.int64)
        bid_scaled = np.round(bid_col.values * 1000000.0).astype(np.int64)
    else:
        ask_scaled = ask_col.values.astype(np.int64)
        bid_scaled = bid_col.values.astype(np.int64)
    vol_arr = vol_col.values.astype(np.uint64)
    return pa.Table.from_arrays(
        [
            dt_arr,
            pa.array(ask_scaled, type=pa.int64()),
            pa.array(bid_scaled, type=pa.int64()),
            pa.array(vol_arr, type=pa.uint64()),
        ],
        schema=TICK_SCHEMA,
    )


def dataframe_to_canonical_m1(df: pd.DataFrame) -> pa.Table:
    """Preserve the source transformation and archive selection rules."""
    if pa is None:
        raise ImportError("pyarrow is required.")
    if df.empty:
        return pa.Table.from_batches([], schema=M1_SCHEMA)
    dt_col = df["DateTime"] if "DateTime" in df.columns else df["timestamp"]
    dt_arr = pa.Array.from_pandas(
        pd.to_datetime(dt_col, utc=True), type=pa.timestamp("ms", tz="UTC")
    )
    o = (df["Open"] if "Open" in df.columns else df["open"]).values.astype(np.float64)
    h = (df["High"] if "High" in df.columns else df["high"]).values.astype(np.float64)
    low_values = (df["Low"] if "Low" in df.columns else df["low"]).values.astype(
        np.float64
    )
    c = (df["Close"] if "Close" in df.columns else df["close"]).values.astype(
        np.float64
    )
    v = (df["Volume"] if "Volume" in df.columns else df["volume"]).values.astype(
        np.uint64
    )
    return pa.Table.from_arrays(
        [
            dt_arr,
            pa.array(o, type=pa.float64()),
            pa.array(h, type=pa.float64()),
            pa.array(low_values, type=pa.float64()),
            pa.array(c, type=pa.float64()),
            pa.array(v, type=pa.uint64()),
        ],
        schema=M1_SCHEMA,
    )


def resolve_required_cdn_archives(
    symbol: str, start_dt: datetime, end_dt: datetime, available_archives: list[str]
) -> list[str]:
    """Preserve the source transformation and archive selection rules."""
    req_years = set(range(start_dt.year, end_dt.year + 1))
    selected = []
    for yr in sorted(req_years):
        yr_zip = f"{yr}.zip"
        if yr_zip in available_archives:
            selected.append(yr_zip)
        else:
            start_m = start_dt.month if yr == start_dt.year else 1
            end_m = end_dt.month if yr == end_dt.year else 12
            for m in range(start_m, end_m + 1):
                m_zip = f"{yr}_{m:02d}.zip"
                if m_zip in available_archives and m_zip not in selected:
                    selected.append(m_zip)
    logger.info("Darwinex archives selected: symbol=%s count=%d", symbol, len(selected))
    return selected


def symbol_catalog() -> list[dict[str, Any]]:
    """Expose the owner script's embedded catalog as source metadata."""
    result = []
    for line in EMBEDDED_DARWINEX_CSV.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        values = line.split(";")
        if len(values) < 8:
            continue
        day, month, year = map(int, values[1].split("."))
        result.append(
            {
                "symbol": values[0].strip().upper(),
                "date_from": date(year, month, day).isoformat(),
                "decimals": int(values[2]),
                "tick_value": float(values[3]),
                "default_spread": float(values[4]),
                "tick_size": float(values[5]),
                "tick_step": float(values[6]),
                "instrument_type": int(values[7]),
            }
        )
    logger.info("Darwinex catalog read: symbols=%d", len(result))
    return result


class DarwinexDefinition(Document):
    """Explicit source identity with source-owned timeframe options."""

    symbol: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    postfix: str = Field(default="", max_length=40, pattern=r"^[A-Za-z0-9_.-]*$")
    timeframe: Literal[
        "TICK", "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"
    ] = "TICK"
    broker: str = "-1"
    instrument: str = ""


class DarwinexDownload(Document):
    """Bounded source window; raw donor endpoints remain provider-owned."""

    dataset_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    date_from: date
    date_to: date
    overwrite: bool = False
    use_hk: bool = False

    @model_validator(mode="after")
    def dates(self) -> DarwinexDownload:
        """Reject inverted or future acquisition windows."""
        if self.date_from > self.date_to or self.date_to > datetime.now(UTC).date():
            raise ValueError("Invalid historical Darwinex range")
        return self


class DarwinexLogPair(Document):
    """A source-ordered pair of uploaded ask and bid logs."""

    ask_base64: str = Field(default="", max_length=8 * 1024 * 1024)
    bid_base64: str = Field(default="", max_length=8 * 1024 * 1024)


class DarwinexImport(Document):
    """Explicit file inputs with source carry-forward across consecutive pairs."""

    dataset_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    pairs: tuple[DarwinexLogPair, ...] = Field(min_length=1, max_length=128)


@dataclasses.dataclass
class DarwinexRuntime:
    """Prepared source runtime with host sessions, jobs and partition custody."""

    market: MarketAccess
    jobs: JobAccess
    network: SourceNetwork
    progress: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)

    def publish(
        self,
        dataset_id: str,
        frame: pd.DataFrame,
        progress: dict[str, Any],
        candles: bool = False,
        overwrite: bool = True,
    ) -> None:
        """Preserve source fixed-point ticks or derived bar partition types."""
        record = self.market.source_definition(dataset_id)
        timeframe = record["timeframe"]
        if timeframe != "TICK" and not candles:
            frame = ticks_to_m1(
                frame["DateTime"].array.as_unit("ms").asi8,
                frame["Ask"].to_numpy(),
                frame["Bid"].to_numpy(),
                frame["Volume"].to_numpy(),
                int(record["options"]["metadata"]["decimals"]),
            )
        if timeframe not in ("TICK", "M1"):
            frame = resample_candles(frame, timeframe)
        periods = frame["DateTime"].dt.strftime(
            "%Y-%m" if timeframe == "TICK" else "%Y"
        )
        revisions = {
            row["period"]: row for row in self.market.source_partitions(dataset_id)
        }
        for period, incoming in frame.groupby(periods):
            table = (
                dataframe_to_canonical_ticks(incoming)
                if timeframe == "TICK"
                else dataframe_to_canonical_m1(incoming)
            )
            prior = revisions.get(str(period))
            if prior:
                old = self.market.read_source_partition(dataset_id, str(period))
                combined = pa.concat_tables([table, old] if overwrite else [old, table])
                stamps = combined.column("DateTime").cast(pa.int64()).to_numpy()
                _, indices = np.unique(stamps, return_index=True)
                table = combined.take(pa.array(indices[np.argsort(stamps[indices])]))
            self.market.publish_source(
                dataset_id,
                str(period),
                table,
                expected_revision=prior["revision"] if prior else 0,
            )
            progress["published_partitions"] += 1
        progress["rows"] += len(frame)
        logger.info(
            "Darwinex rows published: dataset=%s rows=%d", dataset_id, len(frame)
        )

    async def acquire(  # noqa: C901, PLR0912, PLR0915 -- bounded archive selection and complete-window aggregation.
        self, request: DarwinexDownload, progress: dict[str, Any]
    ) -> None:
        """Use source metadata fallback and annual-before-monthly archive choice."""
        record = self.market.source_definition(request.dataset_id)
        symbol = record["underlying"].upper()
        metadata = record["options"]["metadata"]
        start_date = max(request.date_from, date.fromisoformat(metadata["date_from"]))
        start = datetime.combine(start_date, datetime.min.time(), UTC)
        end = datetime.combine(
            request.date_to + timedelta(days=1), datetime.min.time(), UTC
        ) - timedelta(milliseconds=1)
        bases = (
            (CDN_HK_URL, CDN_BASE_URL) if request.use_hk else (CDN_BASE_URL, CDN_HK_URL)
        )
        available: list[str] = []
        selected_base = bases[0]
        for base in bases:
            response = await self.network.get(
                f"{base}/{symbol}/metadata.dat", request_seconds=10
            )
            if response.status == 200 and response.body:
                selected_base = base
                available = [
                    item.strip()
                    for item in response.body.decode().split(";")
                    if item.strip()
                ]
                break
        archives = resolve_required_cdn_archives(symbol, start, end, available)
        if not archives:
            raise ValueError("No Darwinex archives available for this range")
        progress["total_chunks"] = len(archives)
        minute_frames: list[pd.DataFrame] = []
        minute_bytes = 0
        for archive_name in archives:
            async with self.network.archive(
                f"{selected_base}/{symbol}/{archive_name}"
            ) as archive:
                for name in sorted(archive.members()):
                    if not name.endswith(".dat"):
                        continue
                    parts = name.removesuffix(".dat").split("_")
                    if len(parts) >= 3:
                        try:
                            day = date(int(parts[0]), int(parts[1]), int(parts[2]))
                        except ValueError:
                            day = None
                        if day is not None and not start.date() <= day <= end.date():
                            continue
                    frame = await self.jobs.offload(
                        SQBinaryDatDecoder.decode_to_dataframe, archive.read(name)
                    )
                    if frame.empty:
                        continue
                    frame = frame[
                        (frame["DateTime"] >= start) & (frame["DateTime"] <= end)
                    ]
                    if not frame.empty:
                        if record["timeframe"] not in ("TICK", "M1"):
                            minutes = await self.jobs.offload(
                                ticks_to_m1,
                                frame["DateTime"].array.as_unit("ms").asi8,
                                frame["Ask"].to_numpy(),
                                frame["Bid"].to_numpy(),
                                frame["Volume"].to_numpy(),
                                int(metadata["decimals"]),
                            )
                            minute_bytes += int(minutes.memory_usage(deep=True).sum())
                            if minute_bytes > 128 * 1024 * 1024:
                                raise ValueError(
                                    "Derived Darwinex bars exceed job bounds; "
                                    "choose a smaller range"
                                )
                            minute_frames.append(minutes)
                        else:
                            await self.jobs.offload(
                                self.publish,
                                request.dataset_id,
                                frame,
                                progress,
                                False,
                                request.overwrite,
                            )
                    await asyncio.sleep(0)
            progress["completed_chunks"] += 1
        if minute_frames:
            minutes = (
                pd.concat(minute_frames)
                .drop_duplicates("DateTime", keep="last")
                .sort_values("DateTime")
            )
            await self.jobs.offload(
                self.publish,
                request.dataset_id,
                minutes,
                progress,
                True,
                request.overwrite,
            )
        if not progress["rows"]:
            raise ValueError("Darwinex returned no data in this range")

    async def import_logs(
        self, request: DarwinexImport, progress: dict[str, Any]
    ) -> None:
        """Merge real uploaded sides with source carry-forward and volume units."""
        state = None
        frames: list[pd.DataFrame] = []
        for pair in request.pairs:
            ask = (
                base64.b64decode(pair.ask_base64, validate=True)
                if pair.ask_base64
                else None
            )
            bid = (
                base64.b64decode(pair.bid_base64, validate=True)
                if pair.bid_base64
                else None
            )
            times, asks, bids, volumes, state = await self.jobs.offload(
                DarwinexFileImporter.merge_ask_bid_files, ask, bid, state
            )
            if len(times):
                frame = pd.DataFrame(
                    {
                        "DateTime": pd.to_datetime(times, unit="ms", utc=True),
                        "Ask": asks,
                        "Bid": bids,
                        "Volume": volumes,
                    }
                )
                frames.append(frame)
            progress["completed_chunks"] += 1
            await asyncio.sleep(0)
        if frames:
            frame = (
                pd.concat(frames)
                .drop_duplicates("DateTime", keep="last")
                .sort_values("DateTime")
            )
            await self.jobs.offload(self.publish, request.dataset_id, frame, progress)
        if not progress["rows"]:
            raise ValueError("Uploaded Darwinex logs contain no tick rows")

    async def invoke(  # noqa: C901 -- explicit source operations.
        self, operation: str, payload: JsonValue
    ) -> JsonValue:
        """Expose real definitions, source catalog, file/network jobs and status."""
        values = payload if isinstance(payload, dict) else {}
        logger.info("Darwinex operation: %s", operation)
        if operation == "catalog":
            ready = self.market.source_available()
            return cast(
                "JsonValue",
                {
                    "available": ready,
                    "reason": ""
                    if ready
                    else "Script-backed catalog migration is required",
                    "datasets": self.market.source_definitions() if ready else [],
                    "symbols": symbol_catalog(),
                    "schema": DarwinexDefinition.model_json_schema(),
                },
            )
        if operation == "add":
            definition = DarwinexDefinition.model_validate(values)
            metadata = next(
                (
                    row
                    for row in symbol_catalog()
                    if row["symbol"] == definition.symbol.upper()
                ),
                None,
            )
            if metadata is None:
                raise ValueError("Unknown Darwinex symbol")
            dataset_id = self.market.register_source(
                source="Darwinex",
                symbol=definition.symbol.upper() + definition.postfix,
                underlying=definition.symbol.upper(),
                instrument=definition.instrument or definition.symbol.upper(),
                timeframe=definition.timeframe,
                broker=definition.broker,
                options={
                    "parameters": definition.model_dump(mode="json"),
                    "metadata": metadata,
                },
            )
            return {"id": dataset_id}
        if operation in ("download.start", "import.start"):
            progress: dict[str, Any] = {
                "rows": 0,
                "published_partitions": 0,
                "completed_chunks": 0,
                "total_chunks": 0,
            }
            if operation == "download.start":
                download = DarwinexDownload.model_validate(values)
                self.market.source_definition(download.dataset_id)

                async def run() -> None:
                    await self.acquire(download, progress)
            else:
                uploaded = DarwinexImport.model_validate(values)
                self.market.source_definition(uploaded.dataset_id)
                if (
                    sum(
                        len(pair.ask_base64) + len(pair.bid_base64)
                        for pair in uploaded.pairs
                    )
                    > 8 * 1024 * 1024
                ):
                    raise ValueError("Darwinex upload exceeds batch limit")
                progress["total_chunks"] = len(uploaded.pairs)

                async def run() -> None:
                    await self.import_logs(uploaded, progress)

            job = self.jobs.submit(Budget(1, 512 * 1024 * 1024, 3600), run)
            self.progress[job.id] = progress
            return {"job_id": job.id, "state": job.state}
        if operation in ("download.status", "download.cancel"):
            job_id = str(values.get("job_id", ""))
            if operation == "download.cancel":
                self.jobs.cancel(job_id)
            job = self.jobs.status(job_id)
            return cast(
                "JsonValue",
                {"job_id": job.id, "state": job.state, **self.progress[job.id]},
            )
        raise ValueError("Unknown Darwinex operation")

    async def close(self) -> None:
        """Await owned jobs before closing their private source session."""
        await self.jobs.close()
        await self.network.close()
        logger.info("Darwinex source closed")


async def prepare(context: HostCapabilities) -> PreparedContribution:
    """Bind source capabilities without import-time acquisition or mutation."""
    if context.market_data is None or context.jobs is None or context.network is None:
        raise ValueError("Darwinex requires market data, jobs and network capabilities")
    network = context.network.source_session(
        ("https://cdn.strategyquantcdn.com", "https://cdn005.strategyquantcdn.com")
    )
    runtime = DarwinexRuntime(context.market_data, context.jobs, network)
    return PreparedContribution(
        (
            "catalog",
            "add",
            "download.start",
            "import.start",
            "download.status",
            "download.cancel",
        ),
        runtime.invoke,
        runtime.close,
    )
