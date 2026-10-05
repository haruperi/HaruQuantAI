"""Verify visibility behavior and rejection boundaries."""

from typing import Any, cast

from app.workspace.DataManager.Data.visibility import set_visibility


def test_explicit_visibility_preserves_input(dataset):
    changed = set_visibility(dataset, False).unwrap()
    assert changed.visible is False and dataset.visible is True
    assert set_visibility(changed, False).unwrap() == changed
    assert changed.records == dataset.records


def test_invalid_visibility(dataset):
    assert set_visibility(dataset, cast("Any", 1)).error_code == "INVALID_VISIBILITY"
