"""Removal harness coverage is derived from the actual shipping ownership set."""

from pathlib import Path

import pytest
from app.host.packages import scan_packages
from scripts.removal_check import preflight, required_cases

from scripts import removal_check
from tests.host.test_packages import make_package


def test_matrix_includes_every_package_empty_owner_and_empty_host(
    tmp_path: Path,
) -> None:
    make_package(tmp_path, "owner")
    make_package(tmp_path, "other")
    make_package(tmp_path, "child", "test.owner")
    cases = {case.id: case for case in required_cases(scan_packages(tmp_path))}
    assert cases["remove.test.child"].kind == "plugin_removal"
    assert cases["remove.test.owner"].kind == "workspace_cascade"
    assert cases["empty.test.owner"].targets == ("test.child",)
    assert cases["empty.test.other"].targets == ()
    assert set(cases["empty.host"].targets) == {"test.owner", "test.other"}
    assert {case.kind for case in cases.values()} == {
        "baseline",
        "plugin_removal",
        "workspace_cascade",
        "empty_workspace",
        "empty_host",
        "invalid_attachment",
        "activation_failure",
        "disable_reinstall",
        "producer_absence",
        "unsafe_removal",
        "negative_gate",
    }


def test_preflight_rejects_unowned_source_and_broken_counterparts(
    tmp_path: Path,
) -> None:
    document = make_package(tmp_path, "owner")
    assert preflight(tmp_path) == []
    entry = tmp_path / document["ui_entry"]
    stray = entry.with_name("unowned.ts")
    stray.write_text("export const broken = true")
    assert any("unowned:" in issue for issue in preflight(tmp_path))
    entry.unlink()
    assert any("invalid_package:" in issue for issue in preflight(tmp_path))


def test_browser_host_ignores_inherited_installation_and_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Launch and gracefully stop a real host without inherited HARU authority.

    Only the browser runner is intercepted: startup, HTTP readiness, authentication
    and shutdown use the actual server process in a private installation copy.
    """
    import shutil
    import urllib.request

    root = tmp_path / "installation"
    root.mkdir()
    source = Path(__file__).resolve().parents[1]
    shutil.copytree(
        source / "app",
        root / "app",
        ignore=shutil.ignore_patterns("ui", "__pycache__", "workspace", "plugins"),
    )
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    data = tmp_path / "data"
    unrelated = tmp_path / "unrelated"
    monkeypatch.setenv("HARU_DATA_DIR", str(unrelated))
    monkeypatch.setenv("HARU_INSTALLATION_ROOT", str(unrelated))
    monkeypatch.setenv("HARU_PORT", "1")
    observed: list[str] = []

    def browser_probe(
        check_root: Path,
        check_evidence: Path,
        check_id: str,
        command: tuple[str, ...],
        *,
        environment: dict[str, str] | None = None,
    ) -> dict[str, object]:
        assert check_root == root and check_evidence == evidence
        assert environment is not None
        assert environment["HARU_INSTALLATION_ROOT"] == str(root)
        assert "HARU_DATA_DIR" not in environment
        assert "HARU_PORT" not in environment
        assert command[-1] == "package-removal.spec.ts"
        with urllib.request.urlopen(
            environment["HARU_TEST_URL"] + "/api/v1/health", timeout=5
        ) as response:
            assert response.status == 200
        observed.append(check_id)
        return {"status": "pass"}

    monkeypatch.setattr(removal_check, "run_check", browser_probe)
    assert removal_check._browser_check(root, data, evidence)["status"] == "pass"
    assert observed == ["browser_restart_resources"]
    assert data.exists() and not unrelated.exists()
    assert not (root / ".package-operation.lock").exists()
