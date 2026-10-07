"""Data provider re-exports for the Data Manager workspace.

Description:
    Exposes provider adapter interfaces and `ProviderManager` from `connections`.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Provider adapter interfaces and provider manager.

Key Capabilities:
    FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters.

Python API Usage:
    ```python
    from app.workspace.data_manager.providers import (
        BaseDataProvider,
        CancellationToken,
        DownloadRequest,
        ProviderCapabilities,
        ProviderManager,
        RateLimiter,
    )
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.connections --list
    ```
"""

from __future__ import annotations

from app.workspace.data_manager.connections import (
    BaseDataProvider,
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
    ProviderManager,
    RateLimiter,
    SyntheticMockHelper,
)

__all__ = [
    "BaseDataProvider",
    "CancellationToken",
    "DownloadRequest",
    "ProviderCapabilities",
    "ProviderManager",
    "RateLimiter",
    "SyntheticMockHelper",
]
