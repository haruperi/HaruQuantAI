"""Unit and HTTP integration tests for AppWizard (WizardService and routes).

Description:
    Verifies Phase 5.7 (WO-WZ-WORKSPACE-COORDINATOR, Gate G7) requirements:
    - Built-in canonical HSL 1.0 strategy examples catalog (list_examples,
      load_example, category/query filters, cloning, WIZARD_EXAMPLE_NOT_FOUND).
    - Strategy file persistence and loading (save_file, load_file by file_id,
      inline JSON string, inline dict, legacy wizard document auto-upgrade,
      filename sanitization, MRU recent_files tracking, revision bumping, and
      WIZARD_INVALID_STRATEGY / WIZARD_FILE_NOT_FOUND / WIZARD_INVALID_JSON).
    - Retester compilation handoff (save_to_retester producing HSLStrategyDocument
      and compiled StrategyDocument).
    - FastAPI router (create_wizard_router) mounting /algowizard/*, /constants/*,
      and /strategy/* endpoints.

Purpose:
    FEAT-WIZARD-WORKSPACE: Gate G7 verification suite for WizardService and
    create_wizard_router.

Key Capabilities:
    - FR-wizard-workspace-tests: Exercises WizardService and FastAPI routes
      with >80% branch coverage.

Python API Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_workspace.py --no-cov -q

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_workspace.py --no-cov -q
"""

from __future__ import annotations

import json

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.strategy.contracts import StrategyDocument
from app.core.trading.strategy.hsl.compiler import StrategyCompiler
from app.core.trading.strategy.hsl.models import (
    ComparisonConditionNode,
    HSLStrategyDocument,
    HSLStrategyPayload,
    OrderMarketActionNode,
    RuleNode,
)
from app.core.trading.strategy.hsl.validation import StrategyValidator
from app.core.trading.strategy.hsl.value_models import (
    IndicatorExpressionNode,
    ValueLiteralNode,
)
from app.workspace.algo_wizard.catalogue import WizardCatalogueService
from app.workspace.algo_wizard.routes import create_wizard_router
from app.workspace.algo_wizard.strategies import StrategyDocumentService
from app.workspace.algo_wizard.visual_blocks import VisualBlockService
from app.workspace.algo_wizard.workspace import WizardService
from app.workspace.algo_wizard.workspace_models import (
    ListWizardExamplesRequest,
    LoadStrategyFileRequest,
    LoadWizardExampleRequest,
    SaveStrategyFileRequest,
    SaveToRetesterRequest,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError


def _make_invalid_hsl_document() -> HSLStrategyDocument:
    """Create a syntactically valid HSLStrategyDocument that fails semantic validation."""
    return HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id="invalid_strategy",
            name="Invalid Strategy",
            rules=(
                RuleNode(
                    id="bad_rule",
                    name="Bad Rule",
                    when=ComparisonConditionNode(
                        operator="greater_than",
                        left=IndicatorExpressionNode(
                            name="indicator.unknown_nonexistent",
                            params={"period": 14},
                        ),
                        right=ValueLiteralNode(value=50.0, value_type="float"),
                    ),
                    then=(OrderMarketActionNode(side="long"),),
                ),
            ),
        ),
    )


def test_wizard_service_properties_and_examples_catalog() -> None:
    """Verify WizardService collaborator properties and list_examples filtering."""
    svc = WizardService()
    assert isinstance(svc.validator, StrategyValidator)
    assert isinstance(svc.compiler, StrategyCompiler)
    assert isinstance(svc.catalogue_service, WizardCatalogueService)
    assert isinstance(svc.strategy_service, StrategyDocumentService)
    assert isinstance(svc.visual_block_service, VisualBlockService)

    all_resp = svc.list_examples()
    example_ids = [item.example_id for item in all_resp.data]
    assert example_ids == [
        "ema_crossover",
        "rsi_mean_reversion",
        "atr_breakout",
        "mtf_trend_filter",
    ]

    trend_resp = svc.list_examples(ListWizardExamplesRequest(category="TREND"))
    assert [item.example_id for item in trend_resp.data] == ["ema_crossover"]

    query_resp = svc.list_examples(ListWizardExamplesRequest(query="volatility"))
    assert [item.example_id for item in query_resp.data] == ["atr_breakout"]

    empty_resp = svc.list_examples(ListWizardExamplesRequest(query="no_such_tag_xyz"))
    assert empty_resp.data == ()


@pytest.mark.parametrize(
    ("raw_id", "expected_id"),
    [
        ("ema_crossover", "ema_crossover"),
        ("examples/EMA-Crossover.sqx", "ema_crossover"),
        ("rsi_mean_reversion.json", "rsi_mean_reversion"),
        ("atr_breakout", "atr_breakout"),
        ("mtf_trend_filter", "mtf_trend_filter"),
    ],
)
def test_load_example_all_templates_valid_and_cloned(
    raw_id: str,
    expected_id: str,
) -> None:
    """Verify every built-in example loads, validates cleanly, and returns a clone."""
    svc = WizardService()
    resp = svc.load_example(LoadWizardExampleRequest(example_id=raw_id))
    assert resp.data.summary.example_id == expected_id
    report = svc.validator.validate(resp.data.document, raise_on_error=False)
    assert report.valid is True
    assert len(report.issues) == 0


def test_load_example_not_found_raises_domain_error() -> None:
    """Verify load_example raises WIZARD_EXAMPLE_NOT_FOUND for unknown templates."""
    svc = WizardService()
    with pytest.raises(DomainError) as exc_info:
        svc.load_example(LoadWizardExampleRequest(example_id="missing_template"))
    assert exc_info.value.code == "WIZARD_EXAMPLE_NOT_FOUND"


def test_save_and_load_file_roundtrip_and_revisions() -> None:
    """Verify save_file and load_file round-trip, filename sanitization, and MRU."""
    svc = WizardService()
    example_doc = svc.load_example(
        LoadWizardExampleRequest(example_id="ema_crossover")
    ).data.document

    save1 = svc.save_file(
        SaveStrategyFileRequest(
            document=example_doc,
            filename="folder/My EMA Strategy!.sqx",
        )
    )
    assert save1.data.file_id == "My_EMA_Strategy"
    assert save1.data.filename == "My_EMA_Strategy.json"
    assert save1.data.revision == 1
    assert save1.data.recent_files == ("My_EMA_Strategy.json",)

    save2 = svc.save_file(
        SaveStrategyFileRequest(
            document=example_doc,
            file_id="My_EMA_Strategy",
        )
    )
    assert save2.data.revision == 2
    assert save2.data.document_hash == save1.data.document_hash

    # Save a second file to exercise MRU reordering
    rsi_doc = svc.load_example(
        LoadWizardExampleRequest(example_id="rsi_mean_reversion")
    ).data.document
    svc.save_file(SaveStrategyFileRequest(document=rsi_doc, filename="   ...   "))
    assert svc.get_saved_file("strategy") is not None
    assert len(svc.list_saved_files()) == 2

    loaded = svc.load_file(LoadStrategyFileRequest(file_id="My_EMA_Strategy.json"))
    assert loaded.data.strategy.id == example_doc.strategy.id
    assert svc.get_saved_file("My_EMA_Strategy") is not None


def test_load_file_from_inline_payload_and_legacy_upgrade() -> None:
    """Verify load_file supports inline JSON strings, dicts, and legacy payloads."""
    svc = WizardService()
    example_doc = svc.load_example(
        LoadWizardExampleRequest(example_id="atr_breakout")
    ).data.document

    # 1. Inline canonical JSON string
    json_str = json.dumps(example_doc.model_dump(mode="json"))
    loaded_from_str = svc.load_file(LoadStrategyFileRequest(payload=json_str))
    assert loaded_from_str.data.strategy.id == "example_atr_breakout"

    # 2. Inline canonical dict
    loaded_from_dict = svc.load_file(
        LoadStrategyFileRequest(payload=example_doc.model_dump(mode="json"))
    )
    assert loaded_from_dict.data.strategy.id == "example_atr_breakout"

    # 3. Inline legacy wizard payload upgraded automatically
    legacy_payload = {
        "strategy_id": "legacy_rsi_strat",
        "name": "Legacy RSI Strategy",
        "universe": ["GBPUSD"],
        "timeframe": "H1",
        "indicators": {
            "rsi_14": {"type": "rsi", "period": 14},
        },
        "rules": [
            {
                "id": "r1",
                "direction": "LONG",
                "entry": True,
                "conditions": [
                    {
                        "left": "rsi_14",
                        "op": "<",
                        "right": 30,
                    }
                ],
            }
        ],
    }
    upgraded = svc.load_file(LoadStrategyFileRequest(payload=legacy_payload))
    assert upgraded.data.strategy.id == "legacy_rsi_strat"
    assert upgraded.data.strategy.universe.symbols == ("GBPUSD",)


def test_load_and_save_file_error_paths() -> None:
    """Verify error handling for missing source, bad JSON, and invalid HSL AST."""
    svc = WizardService()

    with pytest.raises(ValidationError):
        LoadStrategyFileRequest()

    with pytest.raises(DomainError) as not_found_exc:
        svc.load_file(LoadStrategyFileRequest(file_id="nonexistent_file"))
    assert not_found_exc.value.code == "WIZARD_FILE_NOT_FOUND"

    with pytest.raises(DomainError) as bad_json_exc:
        svc.load_file(LoadStrategyFileRequest(payload="{not-valid-json"))
    assert bad_json_exc.value.code == "WIZARD_INVALID_JSON"

    with pytest.raises(DomainError) as non_obj_exc:
        svc.load_file(LoadStrategyFileRequest(payload="[1, 2, 3]"))
    assert non_obj_exc.value.code == "WIZARD_INVALID_JSON"

    with pytest.raises(DomainError) as bad_schema_exc:
        svc.load_file(
            LoadStrategyFileRequest(
                payload={"schema_version": "9.9.9", "strategy": {"bad": True}}
            )
        )
    assert bad_schema_exc.value.code == "WIZARD_SCHEMA_INVALID"

    invalid_doc = _make_invalid_hsl_document()
    with pytest.raises(DomainError) as save_invalid_exc:
        svc.save_file(SaveStrategyFileRequest(document=invalid_doc, strict=True))
    assert save_invalid_exc.value.code == "WIZARD_INVALID_STRATEGY"

    # Non-strict save & load succeeds even with validation issues
    saved_non_strict = svc.save_file(
        SaveStrategyFileRequest(
            document=invalid_doc,
            filename="non_strict_invalid",
            strict=False,
        )
    )
    assert saved_non_strict.data.file_id == "non_strict_invalid"

    with pytest.raises(DomainError) as load_invalid_exc:
        svc.load_file(
            LoadStrategyFileRequest(file_id="non_strict_invalid", strict=True)
        )
    assert load_invalid_exc.value.code == "WIZARD_INVALID_STRATEGY"

    loaded_non_strict = svc.load_file(
        LoadStrategyFileRequest(file_id="non_strict_invalid", strict=False)
    )
    assert loaded_non_strict.data.strategy.id == "invalid_strategy"


def test_save_to_retester_compiles_and_bundles_strategy() -> None:
    """Verify save_to_retester validates and compiles HSL into a Retester bundle."""
    svc = WizardService()
    mtf_doc = svc.load_example(
        LoadWizardExampleRequest(example_id="mtf_trend_filter")
    ).data.document

    handoff_resp = svc.save_to_retester(
        SaveToRetesterRequest(
            document=mtf_doc,
            retester_project_name="RetesterFX",
        )
    )
    assert handoff_resp.data.handoff_id == "retester-example_mtf_trend_filter-1"
    assert handoff_resp.data.retester_project_name == "RetesterFX"
    assert isinstance(handoff_resp.data.compiled_document, StrategyDocument)
    assert len(svc.list_retester_handoffs()) == 1

    invalid_doc = _make_invalid_hsl_document()
    with pytest.raises(DomainError) as exc_info:
        svc.save_to_retester(SaveToRetesterRequest(document=invalid_doc))
    assert exc_info.value.code == "WIZARD_INVALID_STRATEGY"


def test_wizard_http_routes_end_to_end() -> None:
    """Verify FastAPI routes across /algowizard/*, /constants/*, and /strategy/*."""
    app = FastAPI()
    wizard_svc = WizardService()
    app.include_router(create_wizard_router(wizard_service=wizard_svc))
    client = TestClient(app)

    # 1. GET /AlgoWizard/examples/examples.json & POST /algowizard/examples
    get_ex = client.get(
        "/AlgoWizard/examples/examples.json", params={"category": "trend"}
    )
    assert get_ex.status_code == 200
    assert len(get_ex.json()["data"]) == 1

    post_ex = client.post("/algowizard/examples", json={"request_id": "r-ex"})
    assert post_ex.status_code == 200
    assert len(post_ex.json()["data"]) == 4

    # 2. POST /algowizard/loadExample (200 and 404)
    load_ex = client.post(
        "/algowizard/loadExample",
        json={"request_id": "r-load-ex", "example_id": "ema_crossover"},
    )
    assert load_ex.status_code == 200
    ema_doc_json = load_ex.json()["data"]["document"]

    not_found_ex = client.post(
        "/algowizard/loadExample",
        json={"request_id": "r-404", "example_id": "unknown_ex"},
    )
    assert not_found_ex.status_code == 404

    # 3. POST /algowizard/saveFile, /algowizard/loadFile, /algowizard/saveToRetester
    save_f = client.post(
        "/algowizard/saveFile",
        json={"document": ema_doc_json, "filename": "ema_http.json"},
    )
    assert save_f.status_code == 200
    assert save_f.json()["data"]["file_id"] == "ema_http"

    load_f = client.post("/algowizard/loadFile", json={"file_id": "ema_http"})
    assert load_f.status_code == 200
    assert load_f.json()["data"]["strategy"]["id"] == "example_ema_crossover"

    retester_resp = client.post(
        "/algowizard/saveToRetester",
        json={"document": ema_doc_json},
    )
    assert retester_resp.status_code == 200
    assert retester_resp.json()["data"]["strategy_id"] == "example_ema_crossover"

    # 4. VisualBlockService endpoints on /algowizard/*
    assert client.post("/algowizard/getConfig").status_code == 200
    val_resp = client.post("/algowizard/validate", json={"document": ema_doc_json})
    assert val_resp.status_code == 200
    assert val_resp.json()["data"]["valid"] is True

    neg_resp = client.post(
        "/algowizard/negate",
        json={"condition": {"type": "state", "state": "position.is_flat"}},
    )
    assert neg_resp.status_code == 200
    assert neg_resp.json()["data"]["type"] == "not"

    assert client.post("/algowizard/loadCustomBlocks").status_code == 200
    assert (
        client.post("/algowizard/saveCustomBlocks", json={"blocks": []}).status_code
        == 200
    )
    assert client.post("/algowizard/loadBlockGroups").status_code == 200
    assert (
        client.post("/algowizard/saveBlockGroups", json={"groups": []}).status_code
        == 200
    )

    tf_resp = client.post(
        "/algowizard/addNewTimeframe",
        json={"document": ema_doc_json, "timeframe": "D1"},
    )
    assert tf_resp.status_code == 200
    assert "D1" in tf_resp.json()["data"]["strategy"]["timeframe"]["additional"]

    bad_tf_resp = client.post(
        "/algowizard/addNewTimeframe",
        json={"document": ema_doc_json, "timeframe": "BAD_TF"},
    )
    assert bad_tf_resp.status_code == 400

    res_resp = client.post(
        "/algowizard/checkResources",
        json={"document": ema_doc_json},
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["data"]["ready"] is True

    bt_resp = client.post(
        "/algowizard/backtest",
        json={
            "document": ema_doc_json,
            "backtest_id": "bt-http-1",
            "bars": [
                {
                    "time": 1704110400,
                    "open": 1.1,
                    "high": 1.101,
                    "low": 1.099,
                    "close": 1.1,
                    "volume": 100,
                }
            ],
        },
    )
    assert bt_resp.status_code == 200
    assert (
        client.post(
            "/algowizard/backtestResults",
            json={"backtest_id": "bt-http-1"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/algowizard/stopBacktest",
            json={"backtest_id": "bt-http-1"},
        ).status_code
        == 200
    )

    # 5. /constants/* endpoints
    assert client.post("/constants/getAll").status_code == 200
    assert (
        client.post(
            "/constants/descriptor",
            json={"block_id": "indicator.ema"},
        ).status_code
        == 200
    )
    assert client.post("/constants/commissions").status_code == 200

    # 6. /strategy/* endpoints (including 409 revision conflict)
    add_st = client.post("/strategy/add", json={"document": ema_doc_json})
    assert add_st.status_code == 200
    conflict_st = client.post(
        "/strategy/add",
        json={"document": ema_doc_json, "expected_revision": 99},
    )
    assert conflict_st.status_code == 409

    assert (
        client.post(
            "/strategy/get",
            json={"strategy_id": "example_ema_crossover"},
        ).status_code
        == 200
    )
    assert client.post("/strategy/list").status_code == 200
    assert (
        client.post(
            "/strategy/start",
            json={"strategy_id": "example_ema_crossover"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/strategy/status",
            json={"strategy_id": "example_ema_crossover"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/strategy/stop",
            json={"strategy_id": "example_ema_crossover"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/strategy/remove",
            json={"strategy_id": "example_ema_crossover"},
        ).status_code
        == 200
    )


def test_importing_models_does_not_populate_global_registry() -> None:
    """Importing AlgoWizard models in a fresh subprocess must not seed the global registry."""
    import subprocess
    import sys

    code = (
        "import sys;"
        "from app.core.trading.strategy.hsl.models import HSLStrategyDocument;"
        "from app.core.trading.blocks.registry import block_registry;"
        "sys.exit(0 if len(block_registry.snapshot()) == 0 else 1)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"


def test_wizard_router_lazy_cached_identity() -> None:
    """Repeated access to wizard_router preserves object identity across entry points."""
    from app.workspace.algo_wizard import wizard_router as router_pkg
    from app.workspace.algo_wizard.routes import wizard_router as router_mod
    from fastapi import APIRouter

    assert isinstance(router_pkg, APIRouter)
    assert isinstance(router_mod, APIRouter)
    assert router_pkg is router_mod

    from app.workspace.algo_wizard import wizard_router as router_pkg2

    assert router_pkg is router_pkg2


@pytest.mark.parametrize(
    ("example_id", "expected_hash"),
    [
        (
            "ema_crossover",
            "3fa8ae69ce438f5e22dbe7f5b1f46c295b9ec25a38a5a4bfa0d594f1e86ba822",
        ),
        (
            "rsi_mean_reversion",
            "1d4f90b180a3bbd0f490e00230d4c7cd71457715f0e137575e27091cdacbc974",
        ),
        (
            "atr_breakout",
            "520bc4dfd05ae2a84fe9cb1b276908a68040d6eecdf3cd04c0211dfac0798b29",
        ),
        (
            "mtf_trend_filter",
            "125e1725f96d11254492495539fe2d5fe4f1a40cfcd7f26704ffc3e16bc55a43",
        ),
    ],
)
def test_example_resources_preserve_original_documents(
    example_id: str, expected_hash: str
) -> None:
    """Qualify shipped payloads against hashes captured from the old builders."""
    import hashlib

    from app.workspace.algo_wizard.workspace import _build_default_examples

    payload = _build_default_examples()[example_id].model_dump(mode="json")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == expected_hash
