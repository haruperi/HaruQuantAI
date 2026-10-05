"""Public imports for Historical Dataset Management.

Description:
    Re-export existing operations and their input/result types for feature callers.
    Requirement implementations remain in their own modules. Importing this package
    does not execute operations or configure host logging or persistence.
Purpose:
    FEAT-DATASET-MANAGEMENT: provide a single public import surface.
Key Capabilities:
    Existing FR-DATASET operations are exported without wrappers. Each owning
    module logs its requirement and outcome when called; import itself performs
    no business operation and introduces no additional functional requirement.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data import Dataset, review_records

    result = review_records(Dataset("fx", "EURUSD", "EURUSD"))
    if result.is_success:
        page = result.unwrap()
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data --no-cov
    ```
"""

from app.workspace.DataManager.Data.catalog_browsing import (
    BrowseResult,
    browse_catalog,
)
from app.workspace.DataManager.Data.chart_review import (
    ChartData,
    ChartPoint,
    review_chart,
)
from app.workspace.DataManager.Data.clearing import (
    ClearResult,
    clear_datasets,
)
from app.workspace.DataManager.Data.contracts import (
    BarConvention,
    BarRecord,
    Catalog,
    Dataset,
    Record,
    TickRecord,
)
from app.workspace.DataManager.Data.csv_export import (
    CsvResult,
    export_csv,
)
from app.workspace.DataManager.Data.date_navigation import (
    find_date_index,
)
from app.workspace.DataManager.Data.metadata_editing import (
    InstrumentFacts,
    edit_metadata,
)
from app.workspace.DataManager.Data.quality_analysis import (
    ProblemKind,
    QualityProblem,
    QualitySummary,
    SessionHours,
    analyze_quality,
)
from app.workspace.DataManager.Data.record_correction import (
    correct_records,
)
from app.workspace.DataManager.Data.record_review import (
    RecordPage,
    review_records,
)
from app.workspace.DataManager.Data.removal import (
    RemovalResult,
    remove_datasets,
)
from app.workspace.DataManager.Data.selection import (
    SelectionResult,
    select_datasets,
)
from app.workspace.DataManager.Data.timezone_cloning import (
    clone_timezone,
)
from app.workspace.DataManager.Data.visibility import (
    set_visibility,
)

__all__ = [
    "BarConvention",
    "BarRecord",
    "BrowseResult",
    "Catalog",
    "ChartData",
    "ChartPoint",
    "ClearResult",
    "CsvResult",
    "Dataset",
    "InstrumentFacts",
    "ProblemKind",
    "QualityProblem",
    "QualitySummary",
    "Record",
    "RecordPage",
    "RemovalResult",
    "SelectionResult",
    "SessionHours",
    "TickRecord",
    "analyze_quality",
    "browse_catalog",
    "clear_datasets",
    "clone_timezone",
    "correct_records",
    "edit_metadata",
    "export_csv",
    "find_date_index",
    "remove_datasets",
    "review_chart",
    "review_records",
    "select_datasets",
    "set_visibility",
]
