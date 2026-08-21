# FEAT-DATA-RETRIEVE_BARS — Historical Bars

## Purpose

Retrieve and normalize historical OHLCV bars from the selected `broker.market-data@1` provider, optionally using `data.bar-cache@1` when available.

## Domain

`data`

## Provides

- `data.historical-bars@1`

## Required Capabilities

- `broker.market-data@1`

## Optional Capabilities

- `data.bar-cache@1`

## Configuration

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `default_timeframe` | `str` | `"M1"` | Validated default timeframe configuration |
| `cache_enabled` | `bool` | `True` | Resolve and use `data.bar-cache@1` when it is active |

## Runtime Effects

| Effect | Owner | Disposal |
| :--- | :--- | :--- |
| `HistoricalBars` service binding | `FEAT-DATA-RETRIEVE_BARS` | Generation-safe registry revocation |

## Persistent State

This feature owns no persistent state directly. When caching is enabled, persistence and retention are owned by the feature providing `data.bar-cache@1`.

## Functional Requirements

| Requirement ID | Responsibility | Implementing Symbol | Source File |
| :--- | :--- | :--- | :--- |
| `FR-DATA-VALIDATE_CONFIG` | Validate default timeframe and caching parameters | `HistoricalBarsConfig.from_dict()` | `config.py` |
| `FR-DATA-VALIDATE_REQUEST` | Validate symbol, timeframe, and date boundaries | `validate_historical_request()` | `validate_request.py` |
| `FR-DATA-NORMALIZE_BARS` | Convert broker raw bars into canonical `Bar` DTOs | `normalize_bars()` | `normalize.py` |
| `FR-DATA-RETRIEVE_BARS` | Retrieve bars through the broker contract | `HistoricalBarsService.retrieve()` | `retrieve.py` |
| `FR-DATA-CACHE_BARS` | Read/write an optional complete cache result | `HistoricalBarsService.retrieve()` | `retrieve.py` |

## Failure Behavior

- Missing `broker.market-data@1` → feature is `BLOCKED`.
- Missing `data.bar-cache@1` → feature stays active and retrieves directly from the broker.
- Invalid request parameters → request raises `ValueError` without corrupting runtime state.

## Removal Behavior

Removing this feature makes `data.historical-bars@1` unavailable. Required consumers transition to `BLOCKED`; unrelated capabilities remain active.
