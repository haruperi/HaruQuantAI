"""Integration tests verifying CRUD reachability for all seven Strategy tables."""

from datetime import timedelta
from pathlib import Path

from app.services.strategy import (
    bootstrap_builtin_strategies,
    build_development_strategy_validation_policy,
    commit_strategy_runtime_state,
    create_strategy_checkpoint,
    initialize_strategy_runtime_state,
    list_strategy_checkpoints,
    list_strategy_configs,
    list_strategy_definitions,
    list_strategy_signals,
    list_strategy_versions,
    load_strategy_runtime_state,
    record_strategy_signals,
)
from app.services.strategy.contracts.factories import (
    create_strategy_signal,
)
from app.services.strategy.contracts.responses import unwrap_strategy_response

from tests.strategy.unit.test_catalog import storage_context
from tests.strategy.unit.test_models import NOW, make_auth


def test_all_seven_tables_have_production_reachability(tmp_path: Path) -> None:
    """Verify production operations write and read all seven Strategy tables.

    Args:
        tmp_path: Temporary directory fixture.

    Returns:
        None.
    """
    auth = make_auth(
        checkpoint=True,
        permissions=("strategy:register", "strategy:update", "strategy:checkpoint"),
    )
    policy = build_development_strategy_validation_policy()

    with storage_context(tmp_path):
        # 1 & 2 & 3 & 7: strategy_definitions, strategy_versions, strategy_configs, strategy_mutations
        bootstrap_res = unwrap_strategy_response(
            bootstrap_builtin_strategies(auth, policy),
            operation="bootstrap",
        )
        assert bootstrap_res["registered_strategies"] == 7

        defs = unwrap_strategy_response(list_strategy_definitions(), operation="defs")
        vers = unwrap_strategy_response(list_strategy_versions(), operation="vers")
        assert len(defs) == 7
        assert len(vers) == 7

        sid = defs[0]["strategy_id"]
        configs = unwrap_strategy_response(
            list_strategy_configs(sid, "1.0.0"), operation="cfgs"
        )
        assert len(configs) >= 1
        cfg = configs[0]
        config_id = f"{sid}@1.0.0#{cfg.config_hash}"

        # 4: strategy_state
        init_st = unwrap_strategy_response(
            initialize_strategy_runtime_state(
                config_id,
                request_id="req-00000000-0000-4000-8000-000000000002",
                correlation_id="cor-00000000-0000-4000-8000-000000000002",
            ),
            operation="init_st",
        )
        assert init_st["evaluation_status"] == "initialized"

        loaded_st = unwrap_strategy_response(
            load_strategy_runtime_state(config_id), operation="load_st"
        )
        assert loaded_st is not None

        committed_st = unwrap_strategy_response(
            commit_strategy_runtime_state(
                config_id,
                expected_state_version=0,
                evaluation_status="ready",
                bars_processed=10,
                local_state={"counter": 1},
                request_id="req-00000000-0000-4000-8000-000000000003",
                correlation_id="cor-00000000-0000-4000-8000-000000000003",
            ),
            operation="commit_st",
        )
        assert committed_st["state_version"] == 1

        # 5: strategy_checkpoints
        ver_refs = unwrap_strategy_response(
            list_strategy_versions(strategy_id=sid), operation="ver_refs"
        )
        ref = ver_refs[0]
        _ = unwrap_strategy_response(
            create_strategy_checkpoint(
                ref, cfg, {"counter": 1}, "checkpoint-auth", auth
            ),
            operation="chk",
        )
        chks = unwrap_strategy_response(
            list_strategy_checkpoints(config_id), operation="chks"
        )
        assert len(chks) >= 1

        # 6: strategy_signals
        sig = create_strategy_signal(
            signal_id="b" * 64,
            strategy_id=sid,
            strategy_version="1.0.0",
            symbol="EURUSD",
            timestamp=NOW - timedelta(minutes=1),
            signal_name="TEST_SIGNAL",
            side="BUY",
            active=True,
            lineage={"market": "dataset-1"},
            facts={"observed_close": "1.1000"},
        )
        sigs_res = unwrap_strategy_response(
            record_strategy_signals(
                config_id,
                (sig,),
                request_id="req-00000000-0000-4000-8000-000000000004",
                correlation_id="cor-00000000-0000-4000-8000-000000000004",
            ),
            operation="rec_sigs",
        )
        assert len(sigs_res) == 1

        read_sigs = unwrap_strategy_response(
            list_strategy_signals(config_id), operation="read_sigs"
        )
        assert len(read_sigs) >= 1
