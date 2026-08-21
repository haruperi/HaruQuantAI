# FEAT-DATA-RETRIEVE_BARS — Historical Bars

## Purpose

Retrieve and normalize historical OHLCV price bars across customizable timeframes and symbols from the active broker market data provider.

## Domain

`data`

## Provides

- `data.historical-bars@1`

## Required Capabilities

- `broker.market-data@1`

## Optional Capabilities

None

## Configuration

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `default_timeframe` | `str` | `"M1"` | Fallback timeframe interval (`M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`, `W1`, `MN1`) |

## Runtime Effects

| Effect | Owner | Disposal |
| :--- | :--- | :--- |
| `HistoricalBars` service binding | `FEAT-DATA-RETRIEVE_BARS` | Revoke capability registration from service registry |

## Persistent State

None

## Functional Requirements

| Requirement ID | Responsibility | Implementing Symbol | Source File |
| :--- | :--- | :--- | :--- |
| `FR-DATA-VALIDATE_CONFIG` | Validate default timeframe parameter | `HistoricalBarsConfig.from_dict()` | `config.py` |
| `FR-DATA-VALIDATE_REQUEST` | Validate symbol, timeframe, and chronological date boundaries | `validate_historical_request()` | `validate_request.py` |
| `FR-DATA-NORMALIZE_BARS` | Convert broker-specific raw bar data into canonical `Bar` DTOs | `normalize_bars()`, `normalize_raw_bar()` | `normalize.py` |
| `FR-DATA-RETRIEVE_BARS` | Coordinate bar retrieval through broker market data contract | `HistoricalBarsService.retrieve()` | `retrieve.py` |

## Failure Behavior

- Missing `broker.market-data@1` provider $\rightarrow$ `BLOCKED` state.
- Invalid request parameters $\rightarrow$ Raises `ValueError` without affecting service runtime.

## Removal Behavior

Removing this feature makes `data.historical-bars@1` unavailable. Downstream consumers (e.g. Research, Backtest, Strategies) requiring historical bars transition cleanly to `BLOCKED`.
