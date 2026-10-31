"""Unit and HTTP integration tests for ServletAlgoCloud (CloudExportService).

Description:
    Verifies Phase 5.8 (WO-WZ-CLOUD-EXPORT, Gate G8) requirements:
    - Export target platform discovery (list_export_targets returning all 8
      platforms and their extensions).
    - Strategy import (import_strategy across editor inline HSL/dict/JSON/legacy,
      file via WizardService, databank via databank registry and
      StrategyDocumentService, and backtest_id, plus WIZARD_IMPORT_SOURCE_NOT_FOUND,
      WIZARD_INVALID_JSON, and strict=True WIZARD_INVALID_STRATEGY).
    - Multi-platform strategy export (export_strategy across python, mql4, mql5,
      easylanguage, ninjatrader, jforex, pseudo_code, and hsl_json, plus
      rejection of invalid documents).
    - FastAPI route integration (/algocloud/targets, /algocloud/import, and
      /algocloud/export).

Purpose:
    FEAT-WIZARD-CLOUD-EXPORT: Gate G8 verification suite for CloudExportService.

Key Capabilities:
    - FR-wizard-cloud-export-tests: Exercises CloudExportService and /algocloud/*
      endpoints with >80% branch coverage.

Python API Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_cloud_export.py --no-cov -q

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_cloud_export.py --no-cov -q
"""

from __future__ import annotations

import hashlib
import json

import pytest
from app.core.lib.errors import DomainError
from app.workspace.algo_wizard.cloud_export import CloudExportService
from app.workspace.algo_wizard.cloud_export_models import (
    CloudImportRequest,
    ExportStrategyRequest,
    ExportTargetPlatform,
    ListExportTargetsRequest,
)
from app.workspace.algo_wizard.models import (
    ComparisonConditionNode,
    HSLStrategyDocument,
    HSLStrategyPayload,
    OrderMarketActionNode,
    PositionCloseActionNode,
    RuleNode,
    StateConditionNode,
    TimeframeSpec,
    VariableSpec,
)
from app.workspace.algo_wizard.routes import create_wizard_router
from app.workspace.algo_wizard.strategies_models import AddStrategyRequest
from app.workspace.algo_wizard.value_models import (
    IndicatorExpressionNode,
    ValueLiteralNode,
)
from app.workspace.algo_wizard.workspace import WizardService
from app.workspace.algo_wizard.workspace_models import (
    LoadWizardExampleRequest,
    SaveStrategyFileRequest,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_invalid_document() -> HSLStrategyDocument:
    """Build an HSLStrategyDocument that fails semantic indicator validation."""
    return HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id="bad_export_strat",
            name="Bad Export Strategy",
            rules=(
                RuleNode(
                    id="bad_rule",
                    name="Bad Rule",
                    when=ComparisonConditionNode(
                        operator="greater_than",
                        left=IndicatorExpressionNode(
                            name="indicator.does_not_exist",
                            params={"period": 14},
                        ),
                        right=ValueLiteralNode(value=50.0, value_type="float"),
                    ),
                    then=(OrderMarketActionNode(side="long"),),
                ),
            ),
        ),
    )


def _make_rich_document() -> HSLStrategyDocument:
    """Build a valid HSLStrategyDocument with variables, additional TFs, and disabled rules."""
    return HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id="   ",
            name="Rich Export Strategy",
            description="Rich strategy for multi-platform export verification",
            timeframe=TimeframeSpec(primary="H1", additional=("H4",)),
            variables={
                "trade_count": VariableSpec(
                    type="int",
                    initial=0,
                    description="Trade counter",
                ),
            },
            rules=(
                RuleNode(
                    id="r_buy",
                    name="Buy Rule",
                    priority=10,
                    enabled=True,
                    when=StateConditionNode(state="position.is_flat"),
                    then=(
                        OrderMarketActionNode(side="long", comment="RichBuy"),
                        OrderMarketActionNode(side="short", comment="RichSell"),
                        PositionCloseActionNode(target_side="any", reason="RichExit"),
                    ),
                ),
                RuleNode(
                    id="r_disabled",
                    name="Disabled Rule",
                    priority=20,
                    enabled=False,
                    when=StateConditionNode(state="position.is_long"),
                    then=(PositionCloseActionNode(target_side="long"),),
                ),
            ),
        ),
    )


def test_list_export_targets() -> None:
    """Verify list_export_targets returns all 8 supported platforms and extensions."""
    svc = CloudExportService()
    resp = svc.list_export_targets(ListExportTargetsRequest(request_id="r-targets"))
    by_platform = {item.platform: item.extension for item in resp.data}
    assert by_platform == {
        "python": ".py",
        "mql4": ".mq4",
        "mql5": ".mq5",
        "easylanguage": ".eld",
        "ninjatrader": ".cs",
        "jforex": ".java",
        "pseudo_code": ".txt",
        "hsl_json": ".json",
    }


def test_import_strategy_all_sources_and_errors() -> None:
    """Verify import_strategy from editor, file, databank, and backtest_id."""
    wizard_svc = WizardService()
    cloud_svc = CloudExportService(wizard_service=wizard_svc)
    ema_doc = wizard_svc.load_example(
        LoadWizardExampleRequest(example_id="ema_crossover")
    ).data.document

    # 1. Editor source: HSLStrategyDocument, dict, JSON string, and legacy dict
    imp_doc = cloud_svc.import_strategy(
        CloudImportRequest(source="editor", document=ema_doc)
    )
    assert imp_doc.data.strategy_id == "example_ema_crossover"
    assert imp_doc.data.validation.valid is True

    imp_dict = cloud_svc.import_strategy(
        CloudImportRequest(
            source="editor",
            document=ema_doc.model_dump(mode="json"),
        )
    )
    assert imp_dict.data.document_hash == imp_doc.data.document_hash

    imp_str = cloud_svc.import_strategy(
        CloudImportRequest(
            source="editor",
            document=json.dumps(ema_doc.model_dump(mode="json")),
        )
    )
    assert imp_str.data.strategy_id == "example_ema_crossover"

    legacy_dict = {
        "strategy_id": "legacy_cloud_1",
        "name": "Legacy Cloud Strategy",
        "universe": ["EURUSD"],
        "timeframe": "H1",
        "indicators": {"rsi_14": {"type": "rsi", "period": 14}},
        "rules": [
            {
                "id": "r1",
                "direction": "LONG",
                "entry": True,
                "conditions": [{"left": "rsi_14", "op": "<", "right": 30}],
            }
        ],
    }
    imp_legacy = cloud_svc.import_strategy(
        CloudImportRequest(source="editor", document=legacy_dict, strict=True)
    )
    assert imp_legacy.data.strategy_id == "legacy_cloud_1"

    # 2. File source via WizardService
    wizard_svc.save_file(
        SaveStrategyFileRequest(document=ema_doc, filename="saved_for_cloud.json")
    )
    imp_file = cloud_svc.import_strategy(
        CloudImportRequest(source="file", file_id="saved_for_cloud")
    )
    assert imp_file.data.strategy_id == "example_ema_crossover"

    # 3. Databank source via explicit databank registration and StrategyDocumentService fallback
    cloud_svc.register_databank_strategy("Results", "ema_db_entry", ema_doc)
    imp_db = cloud_svc.import_strategy(
        CloudImportRequest(
            source="databank",
            databank_name="Results",
            strategy_name="ema_db_entry",
        )
    )
    assert imp_db.data.strategy_id == "example_ema_crossover"

    wizard_svc.strategy_service.add_strategy(AddStrategyRequest(document=ema_doc))
    imp_db_fallback = cloud_svc.import_strategy(
        CloudImportRequest(
            source="databank",
            strategy_name="example_ema_crossover",
        )
    )
    assert imp_db_fallback.data.strategy_id == "example_ema_crossover"

    # 4. Backtest source
    cloud_svc.register_backtest_strategy("bt-cloud-001", ema_doc)
    imp_bt = cloud_svc.import_strategy(
        CloudImportRequest(source="backtest_id", backtest_id="bt-cloud-001")
    )
    assert imp_bt.data.strategy_id == "example_ema_crossover"

    # 5. Error paths
    for bad_req in (
        CloudImportRequest(source="editor", document=None),
        CloudImportRequest(source="editor", document="   "),
        CloudImportRequest(source="file", file_id=None),
        CloudImportRequest(source="file", file_id="missing_file"),
        CloudImportRequest(source="databank", strategy_name=None),
        CloudImportRequest(source="databank", strategy_name="missing_strat"),
        CloudImportRequest(source="backtest_id", backtest_id=None),
        CloudImportRequest(source="backtest_id", backtest_id="missing_bt"),
    ):
        with pytest.raises(DomainError) as exc_info:
            cloud_svc.import_strategy(bad_req)
        assert exc_info.value.code == "WIZARD_IMPORT_SOURCE_NOT_FOUND"

    with pytest.raises(DomainError) as bad_json_exc:
        cloud_svc.import_strategy(
            CloudImportRequest(source="editor", document="{invalid-json")
        )
    assert bad_json_exc.value.code == "WIZARD_INVALID_JSON"

    with pytest.raises(DomainError) as non_obj_exc:
        cloud_svc.import_strategy(
            CloudImportRequest(source="editor", document="[1, 2]")
        )
    assert non_obj_exc.value.code == "WIZARD_INVALID_JSON"

    invalid_doc = _make_invalid_document()
    non_strict_res = cloud_svc.import_strategy(
        CloudImportRequest(source="editor", document=invalid_doc, strict=False)
    )
    assert non_strict_res.data.validation.valid is False

    with pytest.raises(DomainError) as strict_exc:
        cloud_svc.import_strategy(
            CloudImportRequest(source="editor", document=invalid_doc, strict=True)
        )
    assert strict_exc.value.code == "WIZARD_INVALID_STRATEGY"


@pytest.mark.parametrize(
    ("platform", "ext", "expected_snippet"),
    [
        ("python", ".py", "class EMACrossover"),
        ("mql4", ".mq4", "extern int MagicNumber"),
        ("mql5", ".mq5", "#include <Trade\\Trade.mqh>"),
        ("easylanguage", ".eld", "Inputs:"),
        ("ninjatrader", ".cs", "namespace NinjaTrader.NinjaScript.Strategies"),
        ("jforex", ".java", "implements IStrategy"),
        ("pseudo_code", ".txt", "STRATEGY: EMA Crossover"),
        ("hsl_json", ".json", '"schema_version": "1.0.0"'),
    ],
)
def test_export_strategy_all_platforms(
    platform: ExportTargetPlatform,
    ext: str,
    expected_snippet: str,
) -> None:
    """Verify export_strategy renders valid code and SHA-256 across all 8 platforms."""
    wizard_svc = WizardService()
    cloud_svc = CloudExportService(wizard_service=wizard_svc)
    ema_doc = wizard_svc.load_example(
        LoadWizardExampleRequest(example_id="ema_crossover")
    ).data.document

    resp = cloud_svc.export_strategy(
        ExportStrategyRequest(
            document=ema_doc,
            target_platform=platform,
        )
    )
    assert resp.data.filename == f"example_ema_crossover{ext}"
    assert expected_snippet in resp.data.content
    expected_sha = hashlib.sha256(resp.data.content.encode("utf-8")).hexdigest()
    assert resp.data.sha256 == expected_sha


def test_export_strategy_rich_branches_and_invalid_document() -> None:
    """Verify rich branches (variables, exits, disabled rules, fallback stem) and errors."""
    cloud_svc = CloudExportService()
    rich_doc = _make_rich_document()

    for plat in ("ninjatrader", "jforex", "pseudo_code"):
        res = cloud_svc.export_strategy(
            ExportStrategyRequest(
                document=rich_doc,
                target_platform=plat,
            )
        )
        assert res.data.filename.startswith("strategy.")
        assert len(res.data.content) > 50

    invalid_doc = _make_invalid_document()
    with pytest.raises(DomainError) as exc_info:
        cloud_svc.export_strategy(
            ExportStrategyRequest(
                document=invalid_doc,
                target_platform="python",
            )
        )
    assert exc_info.value.code == "WIZARD_INVALID_STRATEGY"


def test_algocloud_http_routes() -> None:
    """Verify /algocloud/targets, /algocloud/import, and /algocloud/export over HTTP."""
    app = FastAPI()
    wizard_svc = WizardService()
    cloud_svc = CloudExportService(wizard_service=wizard_svc)
    app.include_router(
        create_wizard_router(
            wizard_service=wizard_svc,
            cloud_export_service=cloud_svc,
        )
    )
    client = TestClient(app)

    targets_resp = client.post("/algocloud/targets")
    assert targets_resp.status_code == 200
    assert len(targets_resp.json()["data"]) == 8

    ema_doc = wizard_svc.load_example(
        LoadWizardExampleRequest(example_id="rsi_mean_reversion")
    ).data.document
    ema_json = ema_doc.model_dump(mode="json")

    imp_resp = client.post(
        "/algocloud/import",
        json={"source": "editor", "document": ema_json},
    )
    assert imp_resp.status_code == 200
    assert imp_resp.json()["data"]["strategy_id"] == "example_rsi_mean_reversion"

    missing_imp = client.post(
        "/algocloud/import",
        json={"source": "file", "file_id": "nonexistent"},
    )
    assert missing_imp.status_code == 404

    exp_resp = client.post(
        "/algocloud/export",
        json={"document": ema_json, "target_platform": "mql5"},
    )
    assert exp_resp.status_code == 200
    assert exp_resp.json()["data"]["filename"] == "example_rsi_mean_reversion.mq5"
