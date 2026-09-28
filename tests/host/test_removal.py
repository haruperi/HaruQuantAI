"""Actual package removal in temporary stores preserves unrelated code and data."""

import pytest
from app.host.packages import scan_packages
from app.host.removal import (
    InstallationLease,
    apply_removal,
    plan_removal,
    restore_removal,
)

from tests.host.test_packages import make_package


def test_workspace_cascade_retains_data_and_other_workspace(tmp_path):
    make_package(tmp_path, "owner")
    make_package(tmp_path, "child", "test.owner")
    make_package(tmp_path, "other")
    data = tmp_path / "data"
    data.mkdir()
    (data / "saved.json").write_bytes(b"published result")
    original = scan_packages(tmp_path)
    plan = plan_removal(tmp_path, original, "test.owner")
    assert set(plan.target_ids) == {"test.owner", "test.child"}
    journal = apply_removal(tmp_path, plan)
    assert [p.id for p in scan_packages(tmp_path).packages] == ["test.other"]
    assert (data / "saved.json").read_bytes() == b"published result"
    restore_removal(tmp_path, journal)
    assert scan_packages(tmp_path).fingerprint == original.fingerprint
    restore_removal(tmp_path, journal)


def test_active_stale_and_forged_plans_fail_closed(tmp_path):
    doc = make_package(tmp_path, "owner")
    plan = plan_removal(tmp_path, scan_packages(tmp_path), "test.owner")
    lease = InstallationLease(tmp_path)
    lease.acquire()
    with pytest.raises(FileExistsError):
        apply_removal(tmp_path, plan)
    lease.release()
    forged = plan.model_copy(update={"files": ("data/saved.json",)})
    with pytest.raises(ValueError, match="closure"):
        apply_removal(tmp_path, forged)
    (tmp_path / doc["ui_entry"]).write_text("changed")
    with pytest.raises(ValueError, match="Stale"):
        apply_removal(tmp_path, plan)


def test_restore_refuses_overwrite(tmp_path):
    doc = make_package(tmp_path, "owner")
    journal = apply_removal(
        tmp_path, plan_removal(tmp_path, scan_packages(tmp_path), "test.owner")
    )
    (tmp_path / doc["ui_entry"]).write_text("new installation")
    with pytest.raises(ValueError, match="overwrite"):
        restore_removal(tmp_path, journal)
