"""Missing ownership cannot silently reduce the shipping qualification set."""

from app.host.packages import scan_packages
from scripts.package_inventory import source_fingerprint, unowned_files

from tests.host.test_packages import make_package


def test_unmanifested_shipping_source_is_a_blocker(tmp_path):
    make_package(tmp_path, "owner")
    assert unowned_files(tmp_path, scan_packages(tmp_path)) == ()
    extra = tmp_path / "app/ui/app/workspace/owner/extra.ts"
    extra.write_text("export const undeclared = true")
    assert unowned_files(tmp_path, scan_packages(tmp_path)) == (
        extra.relative_to(tmp_path).as_posix(),
    )


def test_fingerprint_changes_for_code_but_not_generated_reports(tmp_path):
    doc = make_package(tmp_path, "owner")
    first = source_fingerprint(tmp_path)
    report = tmp_path / ".agents/logs/report.json"
    report.parent.mkdir(parents=True)
    report.write_text("{}")
    assert source_fingerprint(tmp_path) == first
    (tmp_path / doc["ui_entry"]).write_text("changed")
    assert source_fingerprint(tmp_path) != first
