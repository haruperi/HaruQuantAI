"""Tests for the conservative stateless backend shell scaffolder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import scaffold_stateless_feature as scaffold


def _packet() -> dict[str, object]:
    owner = "app/services/demo/demo_lookup"
    contract = "app/contracts/demo/demo_lookup.py"
    acceptance = "docs/dev/evidence/features/FEAT-DEMO-LOOKUP/acceptance.json"
    return {
        "identity": {
            "task_id": "9.99",
            "feature_id": "FEAT-DEMO-LOOKUP",
            "baseline_commit": "a" * 40,
        },
        "task": {
            "task_kind": "feature",
            "task_slug": "demo-lookup",
            "task_name": "Demo lookup",
        },
        "authoring": {"route": "SCAFFOLD_STATELESS_BACKEND"},
        "paths": {
            "domain": "Demo",
            "owner_path": owner,
            "contract_target": contract,
            "evidence_path": acceptance,
            "canonical_spec": "app/services/demo/README.md",
        },
        "contract": {
            "title": "Demo lookup",
            "primary_capability": "demo.demo-lookup@1",
            "public_symbols": ["DemoLookupCapability"],
            "state_ownership": "None; immutable result values only.",
        },
        "requirements": [{"requirement_id": "FR-DEMO-001"}],
        "local_nfrs": [{"requirement_id": "NFR-DEMO-001"}],
        "authorized_write_paths": [
            contract,
            acceptance,
            *[
                f"{owner}/{name}"
                for name in (
                    "__init__.py",
                    "README.md",
                    "config.py",
                    "manifest.py",
                    "feature.py",
                    "_usage.py",
                )
            ],
        ],
        "serialized_integration_write_paths": ["pyproject.toml"],
    }


def test_shell_is_explicitly_incomplete_and_syntactically_valid() -> None:
    """Generated structure cannot masquerade as implementation or acceptance."""
    outputs, proposal = scaffold.build_outputs(_packet())
    acceptance_path = "docs/dev/evidence/features/FEAT-DEMO-LOOKUP/acceptance.json"
    acceptance = json.loads(outputs[acceptance_path])

    assert acceptance["status"] == "IN_PROGRESS"
    assert acceptance["review"]["reviewer_verdict"] == "PENDING"
    assert all(item["status"] == "FAIL" for item in acceptance["requirements"])
    assert all(stage["status"] == "FAIL" for stage in acceptance["stages"].values())
    assert b"NotImplementedError" in outputs["app/services/demo/demo_lookup/feature.py"]
    assert b"RuntimeError" in outputs["app/services/demo/demo_lookup/_usage.py"]
    assert proposal == {
        "demo-demo-lookup": "app.services.demo.demo_lookup.feature:feature"
    }
    for relative, content in outputs.items():
        if relative.endswith(".py") and content:
            compile(content, relative, "exec")


def test_apply_refuses_to_overwrite_any_existing_path(tmp_path: Path) -> None:
    """A repeated or colliding scaffold stops before changing existing work."""
    outputs, _proposal = scaffold.build_outputs(_packet())
    scaffold.apply_outputs(outputs, root=tmp_path)
    before = {relative: (tmp_path / relative).read_bytes() for relative in outputs}

    with pytest.raises(scaffold.ScaffoldError, match="Refusing to overwrite"):
        scaffold.apply_outputs(outputs, root=tmp_path)

    assert {
        relative: (tmp_path / relative).read_bytes() for relative in outputs
    } == before


def test_non_scaffold_route_fails_closed() -> None:
    """Critical/manual/reuse packets cannot invoke this generator."""
    packet = _packet()
    packet["authoring"] = {"route": "NO_AUTOMATIC_SCAFFOLD"}

    with pytest.raises(scaffold.ScaffoldError, match="does not authorize"):
        scaffold.build_outputs(packet)


def test_registration_requires_serialized_integrator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The shared entry-point file cannot be edited by an ordinary draft worker."""
    packet = tmp_path / "packet.json"
    packet.write_text(json.dumps(_packet()), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "scaffold_stateless_feature.py",
            "--task-packet",
            str(packet),
            "--apply",
            "--apply-registration",
        ],
    )

    assert scaffold.main() == 1


def test_serialized_registration_replaces_only_pyproject(tmp_path: Path) -> None:
    """Integrator registration may update its shared file without broad overwrite."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "demo"\nversion = "0.1"\n\n'
        '[project.entry-points."haruquantai.features"]\n',
        encoding="utf-8",
    )
    outputs, proposal = scaffold.build_outputs(_packet())
    outputs["pyproject.toml"] = scaffold._registration_bytes(pyproject, proposal)

    scaffold.apply_outputs(
        outputs,
        root=tmp_path,
        replace_paths=frozenset({"pyproject.toml"}),
    )

    assert (
        'demo-demo-lookup = "app.services.demo.demo_lookup.feature:feature"'
        in pyproject.read_text(encoding="utf-8")
    )
