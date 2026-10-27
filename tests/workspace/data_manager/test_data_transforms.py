"""Clock clones publish their own prices and preserve source data."""

import pandas as pd
from app.host.jobs import JobContext
from app.workspace.data_manager.data.review import DatasetReview
from app.workspace.data_manager.data.transforms import clone_to_timezone
from app.workspace.data_manager.logs import Logs


def test_fixed_shift_copies_prices_and_keeps_source(recorded_history):
    gateway, identifier, root = recorded_history
    before = DatasetReview(gateway, identifier).frame()
    result = clone_to_timezone(
        JobContext("clone-test", root / "clone-job"),
        gateway,
        {"dataset_id": identifier, "shift_hours": 3, "postfix": "_shifted"},
        Logs(),
    )
    after = DatasetReview(gateway, result["dataset_id"]).frame()
    assert after.index[0] == before.index[0] + pd.Timedelta(hours=3)
    assert after.Close.tolist() == before.Close.tolist()
    pd.testing.assert_frame_equal(before, DatasetReview(gateway, identifier).frame())
