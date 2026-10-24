from app.workspace.data_manager.cli import DataCLI
from app.workspace.data_manager.data import Data


def test_data_overview_and_datasets_standard_response() -> None:
    data_svc = Data()
    overview_resp = data_svc.overview()
    assert isinstance(overview_resp, dict)
    assert overview_resp["success"] is True
    assert overview_resp["metadata"]["operation"] == "data.overview"
    assert "datasets_count" in overview_resp["data"]
    assert "total_bars" in overview_resp["data"]
    assert overview_resp["data"]["datasets_count"] >= 0

    list_resp = data_svc.list()
    assert isinstance(list_resp, dict)
    assert list_resp["success"] is True
    assert list_resp["metadata"]["operation"] == "data.list"
    assert isinstance(list_resp["data"], list)
    assert len(list_resp["data"]) == overview_resp["data"]["datasets_count"]

    formatted = DataCLI.format_data_dashboard(overview_resp, list_resp)
    assert "Live Database Overview" in formatted
    assert "Saved Datasets Catalog" in formatted
