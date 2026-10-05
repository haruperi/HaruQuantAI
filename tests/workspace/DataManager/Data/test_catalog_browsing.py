"""Verify catalog browsing behavior and rejection boundaries."""

from app.workspace.DataManager.Data.catalog_browsing import browse_catalog


def test_combined_filters_and_counts(catalog):
    result = browse_catalog(
        catalog,
        text="eur",
        source_id="feed",
        asset_type="forex",
        broker_id="broker",
        group="majors",
    ).unwrap()
    assert result.count == 1 and result.datasets[0].id == "fx"
    assert browse_catalog(catalog, text="APPLE").unwrap().datasets[0].id == "stock"


def test_order_and_empty_filters(catalog):
    assert [item.id for item in browse_catalog(catalog).unwrap().datasets] == [
        "stock",
        "fx",
    ]
    for kwargs in [
        {"source_id": "missing"},
        {"asset_type": "missing"},
        {"broker_id": "missing"},
        {"group": "missing"},
    ]:
        assert browse_catalog(catalog, **kwargs).unwrap().count == 0
    assert len(catalog.datasets) == 2
