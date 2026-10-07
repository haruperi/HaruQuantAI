"""Data Manager workspace home, overview metrics, and quick actions.

Description:
    Provides workspace overview metrics, aggregate catalog statistics, storage
    utilization summaries, and quick action projections for the Data Manager
    workspace home screen, mirroring SQX DataManagerHome.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Central workspace home dashboard and summary metrics.

Key Capabilities:
    - FR-WORKSPACE-DATAMGR-HOME: Compile and serve aggregate status summaries.
      Associated: `[DataManagerHomeService.get_overview()]`
      Logging: Emits DEBUG when workspace home metrics are queried.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.home import DataManagerHomeService

    db = DatabaseManager(":memory:")
    db.initialize()
    home_service = DataManagerHomeService(db)
    overview = home_service.get_overview()
    print(f"Total datasets: {overview.datasets_count}")
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.home --summary
    ```
"""

from __future__ import annotations

import argparse
import sys

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager, PersistenceError

logger = get_logger(__name__)


class WorkspaceOverview(BaseModel):
    """Aggregate statistics for Data Manager workspace home view."""

    model_config = ConfigDict(frozen=True)

    workspace_name: str = Field(default="Data Manager")
    datasets_count: int = Field(default=0, ge=0)
    instruments_count: int = Field(default=0, ge=0)
    sessions_count: int = Field(default=0, ge=0)
    baskets_count: int = Field(default=0, ge=0)
    active_providers_count: int = Field(default=0, ge=0)
    total_bars: int = Field(default=0, ge=0)


class DataManagerHomeService:
    """Service compiling Data Manager workspace dashboard and status summaries."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize home service with host DatabaseManager."""
        self._db = db

    def get_overview(self, active_providers_count: int = 0) -> WorkspaceOverview:
        """Compute authoritative summary statistics for workspace home.

        Fires FR-WORKSPACE-DATAMGR-HOME.
        """
        datasets_count = self._db.datasets.count()
        instruments_count = self._db.instruments.count()

        total_bars = 0
        try:
            with self._db.connection(query_only=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT SUM(bars) FROM datamgr_datasets;")
                val = cur.fetchone()
                if val and val[0] is not None:
                    total_bars = int(val[0])
        except PersistenceError, OSError, ValueError:
            total_bars = 0

        sessions_count = len(self._db.sessions.list_sessions(limit=5000))

        baskets_count = 0
        try:
            with self._db.connection(query_only=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM datamgr_stock_group;")
                b_val = cur.fetchone()
                if b_val and b_val[0] is not None:
                    baskets_count = int(b_val[0])
        except PersistenceError, OSError, ValueError:
            baskets_count = 0

        logger.debug(
            "FR-WORKSPACE-DATAMGR-HOME: Computed workspace overview "
            "(datasets=%d, instruments=%d, bars=%d)",
            datasets_count,
            instruments_count,
            total_bars,
            extra={
                "datasets": datasets_count,
                "instruments": instruments_count,
                "total_bars": total_bars,
                "fr_id": "FR-WORKSPACE-DATAMGR-HOME",
            },
        )

        return WorkspaceOverview(
            datasets_count=datasets_count,
            instruments_count=instruments_count,
            sessions_count=sessions_count,
            baskets_count=baskets_count,
            active_providers_count=active_providers_count,
            total_bars=total_bars,
        )


def main() -> int:
    """CLI tool for querying Data Manager workspace home overview."""
    parser = argparse.ArgumentParser(description="Query workspace overview")
    parser.add_argument("--summary", action="store_true", help="Print summary")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = DataManagerHomeService(db)

    overview = service.get_overview()
    if args.summary:
        print(
            f"Summary: {overview.datasets_count} datasets, {overview.total_bars:,} bars"
        )
    else:
        print("=== Data Manager Workspace Overview ===")
        print(f"  Datasets:         {overview.datasets_count}")
        print(f"  Total Bars:       {overview.total_bars:,}")
        print(f"  Instruments:      {overview.instruments_count}")
        print(f"  Trading Sessions: {overview.sessions_count}")
        print(f"  Baskets:          {overview.baskets_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
