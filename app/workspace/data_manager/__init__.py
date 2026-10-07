"""Data Manager workspace for quantitative data management and discovery.

Description:
    Authoritative Data Manager workspace providing end-to-end quantitative
    market data lifecycle management, instrument specifications, trading
    sessions, multi-symbol baskets, broker profiles, custom time series,
    CFTC COT reports, quality auditing, timeframe transformations, and dynamic
    data source provider routing.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Central Data Manager workspace architecture
    mirroring StrategyQuant X (SQX-145) workspace organization.

Key Capabilities:
    FR-WORKSPACE-DATAMGR-CORE: Unified workspace module exports and coordination.

Python API Usage:
    ```python
    from app.workspace.data_manager import create_data_router

    router = create_data_router(db_manager)
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.routes --help
    ```
"""

from __future__ import annotations

from app.workspace.data_manager.routes import create_data_router

__all__ = ["create_data_router"]
