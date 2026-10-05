"""Verify selection behavior and rejection boundaries."""

from app.workspace.DataManager.Data.selection import select_datasets


def test_selection_order_and_busy_exclusion(catalog):
    result = select_datasets(catalog, ("stock", "fx"), busy_ids={"fx"}).unwrap()
    assert [item.id for item in result.datasets] == ["stock"]
    assert result.excluded_ids == ("fx",)
    assert select_datasets(catalog, ()).unwrap().datasets == ()
    assert select_datasets(catalog, ("fx",), busy_ids={"fx"}).unwrap().datasets == ()


def test_selection_rejects_unknown_and_duplicates(catalog):
    assert select_datasets(catalog, ("fx", "fx")).error_code == "DUPLICATE_SELECTION"
    assert select_datasets(catalog, ("fx", "missing")).error_code == "UNKNOWN_DATASET"
    assert (
        select_datasets(catalog, ("fx",), busy_ids={"missing"}).error_code
        == "UNKNOWN_BUSY_DATASET"
    )
