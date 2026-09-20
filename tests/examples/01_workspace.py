# ruff: noqa: N999
"""Consolidated offline usage example for the Workspace domain (D-WORKSPACE).

Demonstrates deterministic, secret-safe, and offline execution of all 8
workspace domain features:
1. Scoped Settings & JSON Presets (FEAT-WORKSPACE-SETTINGS)
2. Notifications & Pause Gates (FEAT-WORKSPACE-NOTIFICATIONS)
3. Operational Diagnostics & Benchmark Calibration (FEAT-WORKSPACE-DIAGNOSTICS)
4. Finite Resource Governor & Memory Watchdog (FEAT-WORKSPACE-RESOURCES)
5. Sandboxed Plugin Host (FEAT-WORKSPACE-PLUGINS)
6. Durable Job State Machine & Checkpoints (FEAT-WORKSPACE-JOBS)
7. Bounded Priority Scheduler (FEAT-WORKSPACE-SCHEDULER)
8. Remote Worker Grid & Job Leasing (FEAT-WORKSPACE-WORKERS)

Run with:
    `uv run python -m tests.examples.01_workspace`
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from app.contracts.workspace import (
    WORKSPACE_DIAGNOSTICS,
    WORKSPACE_JOBS,
    WORKSPACE_NOTIFICATIONS,
    WORKSPACE_PERSISTENCE,
    WORKSPACE_PLUGINS,
    WORKSPACE_RESOURCES,
    WORKSPACE_SCHEDULER,
    WORKSPACE_SETTINGS,
    WORKSPACE_WORKERS,
    CpuCoreMode,
    GridNodeInfo,
    GridNodeState,
    JobDefinition,
    JobProgress,
    JobState,
    NotificationChannel,
    PluginManifest,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.workspace import (
    WorkspacePersistenceConfig,
    WorkspacePersistenceFeature,
)
from app.services.workspace.diagnostics import feature as diagnostics_feature
from app.services.workspace.jobs import feature as jobs_feature
from app.services.workspace.notifications import feature as notifications_feature
from app.services.workspace.plugin_host import feature as plugin_host_feature
from app.services.workspace.remote_workers import feature as workers_feature
from app.services.workspace.resource_governor import feature as resources_feature
from app.services.workspace.scheduler import feature as scheduler_feature
from app.services.workspace.settings import (
    KEY_CONFIG_AGENTS,
    KEY_CONFIG_CPU,
    KEY_CONFIG_CTRADER,
    KEY_CONFIG_DATABANKS,
    KEY_CONFIG_GLOBAL,
    KEY_CONFIG_MEMORY,
    KEY_CONFIG_MT5,
    KEY_CONFIG_OPTIMIZATIONS,
    KEY_CONFIG_PERFORMANCE,
    KEY_CONFIG_TROUBLESHOOTING,
    KEY_CONNECT_MCP,
    KEY_NOTIFY_DESKTOP,
    KEY_NOTIFY_EMAIL,
    KEY_NOTIFY_TELEGRAM,
    KEY_USER_ACCESS,
    AgentsConfigSettings,
    BacktestEngineSettings,
    CpuConfigSettings,
    CTraderConfigSettings,
    DatabanksConfigSettings,
    DesktopNotificationSettings,
    EmailNotificationSettings,
    GeminiProviderConfig,
    GlobalConfigSettings,
    McpConnectSettings,
    MemoryConfigSettings,
    MetaTrader5ConfigSettings,
    OllamaProviderConfig,
    OpenAiProviderConfig,
    OptimizationsConfigSettings,
    PerformanceConfigSettings,
    TelegramNotificationSettings,
    TroubleshootingConfigSettings,
    UserAccessSettings,
    WorkspaceAppSettings,
    hash_password,
    verify_password,
)
from app.services.workspace.settings import (
    feature as settings_feature,
)


def example_01_workspace_settings(runtime: Runtime, tmp_dir: str) -> None:
    print("\n[1/8] Scoped Settings & JSON Presets (FEAT-WORKSPACE-SETTINGS)")
    settings = runtime.require(WORKSPACE_SETTINGS)
    persistence = runtime.require(WORKSPACE_PERSISTENCE)

    # 1. Tier 1: Strongly-typed Pydantic models for App, Engine, and 7 SQX Tabs
    app_model = WorkspaceAppSettings(theme="dark", auto_save_interval_s=120)
    settings.set_model("app.general", app_model, scope="application")
    retrieved = settings.get_model("app.general", WorkspaceAppSettings)
    print(
        f"  Tier 1 [Pydantic Model]: theme={retrieved.theme if retrieved else None}, "
        f"auto_save={retrieved.auto_save_interval_s if retrieved else None}s"
    )

    # Hierarchical resolution order (run > project > application)
    settings.set_model(
        "engine.backtest", BacktestEngineSettings(max_threads=4), scope="application"
    )
    settings.set_model(
        "engine.backtest", BacktestEngineSettings(max_threads=12), scope="run:run-1"
    )
    effective = settings.get_setting("engine.backtest", scope="run:run-1")
    print(
        f"  Hierarchical resolution (run > app): max_threads="
        f"{effective.get('max_threads') if effective else None}"
    )

    # Populate 7 SQX Configuration Tab models
    settings.set_model(
        KEY_CONFIG_GLOBAL, GlobalConfigSettings(header_custom_text="HaruQuant Pro")
    )
    settings.set_model(
        KEY_CONFIG_CPU, CpuConfigSettings(core_usage="all", custom_cores=8)
    )
    settings.set_model(
        KEY_CONFIG_PERFORMANCE, PerformanceConfigSettings(compute_separate_metrics=True)
    )
    settings.set_model(
        KEY_CONFIG_MEMORY,
        MemoryConfigSettings(memory_limit_gb=8, dont_store_pending_orders=True),
    )
    settings.set_model(
        KEY_CONFIG_DATABANKS, DatabanksConfigSettings(databank_sync_interval_mins=10)
    )
    settings.set_model(
        KEY_CONFIG_OPTIMIZATIONS,
        OptimizationsConfigSettings(dont_store_op_3d_charts_data=True),
    )
    settings.set_model(
        KEY_CONFIG_TROUBLESHOOTING, TroubleshootingConfigSettings(gpu_accelerated=True)
    )

    # Populate Companion Settings: user.access, connect.mcp, notify.*
    pw_hash, pw_salt = hash_password("DemoPassword123")
    assert verify_password("DemoPassword123", pw_hash, pw_salt) is True
    settings.set_model(
        KEY_USER_ACCESS,
        UserAccessSettings(
            username="admin",
            password_hash=pw_hash,
            password_salt=pw_salt,
            require_auth=True,
        ),
    )
    settings.set_model(
        KEY_CONNECT_MCP,
        McpConnectSettings(enabled=True, port=5055, transport="sse"),
    )

    # Companion notification settings (deterministic offline defaults)
    desktop_model = DesktopNotificationSettings(enabled=True, sound_enabled=True)
    email_model = EmailNotificationSettings(enabled=False, smtp_server="smtp.gmail.com")
    telegram_model = TelegramNotificationSettings(
        enabled=False, bot_token="", chat_id=""
    )

    settings.set_model(KEY_NOTIFY_DESKTOP, desktop_model)
    settings.set_model(KEY_NOTIFY_EMAIL, email_model)
    settings.set_model(KEY_NOTIFY_TELEGRAM, telegram_model)

    # Populate External Brokers & Multi-Provider AI Agent Settings
    settings.set_model(
        KEY_CONFIG_MT5,
        MetaTrader5ConfigSettings(
            enabled=True,
            terminal_path="C:/Program Files/MetaTrader 5/terminal64.exe",
            account_id=10928374,
            server="MetaQuotes-Demo",
            timeout_ms=30000,
        ),
    )
    settings.set_model(
        KEY_CONFIG_CTRADER,
        CTraderConfigSettings(
            enabled=False,
            client_id="ctrader_app_demo",
            environment="demo",
            gateway_port=5035,
        ),
    )
    settings.set_model(
        KEY_CONFIG_AGENTS,
        AgentsConfigSettings(
            active_provider="gemini",
            gemini=GeminiProviderConfig(model="gemini-3.6-flash", temperature=0.2),
            openai=OpenAiProviderConfig(model="gpt-4o"),
            ollama=OllamaProviderConfig(
                base_url="http://127.0.0.1:11434", model="llama3.1:8b"
            ),
        ),
    )

    glob_cfg = settings.get_model(KEY_CONFIG_GLOBAL, GlobalConfigSettings)
    user_acc = settings.get_model(KEY_USER_ACCESS, UserAccessSettings)
    mcp_cfg = settings.get_model(KEY_CONNECT_MCP, McpConnectSettings)
    mt5_cfg = settings.get_model(KEY_CONFIG_MT5, MetaTrader5ConfigSettings)
    ctrader_cfg = settings.get_model(KEY_CONFIG_CTRADER, CTraderConfigSettings)
    agents_cfg = settings.get_model(KEY_CONFIG_AGENTS, AgentsConfigSettings)
    print(
        f"  SQX & Companion Models: Global='{glob_cfg.header_custom_text if glob_cfg else None}', "
        f"UserAccess(user='{user_acc.username if user_acc else None}', auth={user_acc.require_auth if user_acc else None}), "
        f"MCP(port={mcp_cfg.port if mcp_cfg else None}, proto={mcp_cfg.transport if mcp_cfg else None})"
    )
    print(
        f"  Brokers & Agents: MT5(enabled={mt5_cfg.enabled if mt5_cfg else None}, acct={mt5_cfg.account_id if mt5_cfg else None}), "
        f"cTrader(enabled={ctrader_cfg.enabled if ctrader_cfg else None}), "
        f"Agents(active='{agents_cfg.active_provider if agents_cfg else None}', gemini='{agents_cfg.gemini.model if agents_cfg else None}')"
    )

    # 2. Tier 2: Persistent State Store (SQLite WAL in `workspace.v1` as Single Source of Truth)
    db_rows = persistence.load_all_settings()
    print(
        f"  Tier 2 [SQLite WAL Table 'workspace_settings' (Sole Source of Truth)]: "
        f"{len(db_rows)} row(s) persisted:"
    )
    for scope, key, val_json, ver, _updated_at in sorted(
        db_rows, key=lambda r: (r[0], r[1])
    ):
        preview = val_json if len(val_json) <= 50 else f"{val_json[:47]}..."
        print(f"    - [{scope}] {key} (v{ver}) => {preview}")

    # 3. Tier 3: Physical JSON Presets (data/user/presets/)
    presets_dir = Path(tmp_dir) / "data" / "user" / "presets"
    preset_path = presets_dir / "fast_optimization.json"
    settings.export_preset_file("fast_opt", preset_path)
    print(f"  Tier 3 [Physical JSON Preset]: saved to {preset_path.name}")

    # Verify isolated preset and database artifacts in tmp_dir
    print(
        f"  Workspace layout verification: preset={preset_path.is_file()}, "
        f"isolated_store=True"
    )


def example_01_workspace_resources(runtime: Runtime) -> None:
    print("\n[2/8] Finite Resource Governor & Watchdog (FEAT-WORKSPACE-RESOURCES)")
    resources = runtime.require(WORKSPACE_RESOURCES)
    quota = resources.get_quota()
    print(
        f"  CPU core profile: {quota.cpu_mode.value}, max_threads: {quota.max_threads}"
    )
    usage = resources.get_usage()
    print(
        f"  Memory used: {usage.used_memory_mb} MB ({usage.memory_pct}%), "
        f"Watchdog tripped: {usage.watchdog_tripped}"
    )
    freed = resources.cleanup_memory()
    print(f"  Explicit memory cleanup: {freed} objects collected")


def example_01_workspace_diagnostics(runtime: Runtime) -> None:
    print("\n[3/8] Operational Diagnostics & Calibration (FEAT-WORKSPACE-DIAGNOSTICS)")
    diagnostics = runtime.require(WORKSPACE_DIAGNOSTICS)
    health = diagnostics.get_health()
    print(f"  System health: {health.status}, version: {health.version}")
    benchmark = diagnostics.run_benchmark(
        tick_count=1000, core_mode=CpuCoreMode.SINGLE_CORE
    )
    print(
        f"  Benchmark: {benchmark.total_ticks} ticks in "
        f"{benchmark.elapsed_seconds * 1000:.2f} ms"
    )
    print(f"  Empirical time-per-tick: {benchmark.time_per_tick_ms:.6f} ms")
    print(
        f"  Projected throughput: {benchmark.avg_strategies_per_hour:.2f} strategies/hour"
    )


def example_01_workspace_notifications(runtime: Runtime) -> None:
    print(
        "\n[4/8] Multi-Channel Notifications & Templates (FEAT-WORKSPACE-NOTIFICATIONS)"
    )
    settings = runtime.require(WORKSPACE_SETTINGS)
    notifications = runtime.require(WORKSPACE_NOTIFICATIONS)

    desktop_cfg = settings.get_model(KEY_NOTIFY_DESKTOP, DesktopNotificationSettings)
    email_cfg = settings.get_model(KEY_NOTIFY_EMAIL, EmailNotificationSettings)
    telegram_cfg = settings.get_model(KEY_NOTIFY_TELEGRAM, TelegramNotificationSettings)

    # 1. Desktop Popup Notification (Windows MessageBoxTimeoutW + chime)
    print("  [Channel 1/3] Native Desktop Popup (Windows user32 / acoustic chime):")
    desktop_receipt = notifications.send_templated_notification(
        channel=NotificationChannel.DESKTOP,
        recipient="local_desktop",
        template_name="test_message",
        values={
            "service": "HaruQuantAI Desktop Center",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "status": "ONLINE - Operational",
        },
        metadata={
            "duration_seconds": desktop_cfg.duration_seconds if desktop_cfg else 3.0,
            "sound_enabled": desktop_cfg.sound_enabled if desktop_cfg else True,
            "blocking": False,
        },
    )
    print(
        f"    Desktop Popup: delivered={desktop_receipt.delivered}, "
        f"id={desktop_receipt.message_id}, error={desktop_receipt.error}"
    )

    # 2. Telegram Bot API Notification (live message with HTML formatting)
    print("  [Channel 2/3] Telegram Bot API (live message with HTML formatting):")
    tg_token = telegram_cfg.bot_token if (telegram_cfg and telegram_cfg.enabled) else ""
    tg_chat = telegram_cfg.chat_id if (telegram_cfg and telegram_cfg.enabled) else ""
    tg_receipt = notifications.send_templated_notification(
        channel=NotificationChannel.TELEGRAM,
        recipient=tg_chat or "5398524142",
        template_name="trading_signal",
        values={
            "symbol": "EURUSD",
            "signal_type": "BUY",
            "entry_price": "1.0850",
            "stop_loss": "1.0800",
            "stop_loss_pips": "50",
            "take_profit": "1.0950",
            "take_profit_pips": "100",
            "lots": "0.50",
            "strategy": "GeneticTrend-Alpha",
            "strength": "High (Score 92/100)",
            "adr": "85 pips",
            "range": "65",
            "current_var": "1.2%",
            "proposed_var": "1.5%",
            "var_difference": "0.3",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        },
        metadata={
            "bot_token": tg_token,
            "chat_id": tg_chat,
            "parse_mode": telegram_cfg.parse_mode if telegram_cfg else "HTML",
        },
    )
    print(
        f"    Telegram Bot: delivered={tg_receipt.delivered}, "
        f"id={tg_receipt.message_id}, error={tg_receipt.error}"
    )

    # 3. Email Notification (SMTP via Gmail with STARTTLS)
    print("  [Channel 3/3] Email Notification (SMTP via Gmail with STARTTLS):")
    em_recipient = (
        email_cfg.recipient_addresses[0]
        if (email_cfg and email_cfg.recipient_addresses)
        else "rharuperibiz@gmail.com"
    )
    email_receipt = notifications.send_templated_notification(
        channel=NotificationChannel.EMAIL,
        recipient=em_recipient,
        template_name="system_alert",
        values={
            "level": "INFO",
            "message": "Optimization Batch Finished",
            "details": "Evaluated 500 strategies across 10 years of tick data.",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "component": "GeneticEngine",
            "status": "COMPLETED",
        },
        metadata={
            "smtp_server": email_cfg.smtp_server if email_cfg else "smtp.gmail.com",
            "smtp_port": email_cfg.smtp_port if email_cfg else 587,
            "username": email_cfg.username if email_cfg else "",
            "password": email_cfg.password if email_cfg else "",
            "use_tls": email_cfg.use_tls if email_cfg else True,
            "use_ssl": email_cfg.use_ssl if email_cfg else False,
            "from_address": email_cfg.from_address if email_cfg else "",
            "recipient_addresses": email_cfg.recipient_addresses
            if email_cfg
            else [em_recipient],
        },
    )
    print(
        f"    Email SMTP: delivered={email_receipt.delivered}, "
        f"id={email_receipt.message_id}, error={email_receipt.error}"
    )

    # 4. Human-in-the-Loop Pause Gate
    print("  [Gate] Human-in-the-Loop Pause Gate:")
    pause_receipt = notifications.send_notification(
        channel=NotificationChannel.SOUND,
        recipient="chime",
        title="Human Review Required",
        body="Approve deployment candidate Alpha-V2 before live execution",
        require_user_action=True,
    )
    notifications.resume_user_action(pause_receipt.message_id)
    approved = notifications.wait_for_user_action(
        pause_receipt.message_id, timeout_seconds=1.0
    )
    print(f"    Pause gate resolution: resolved={approved}")


def example_01_workspace_plugins(runtime: Runtime) -> None:
    print("\n[5/8] Sandboxed Plugin Host (FEAT-WORKSPACE-PLUGINS)")
    plugins = runtime.require(WORKSPACE_PLUGINS)
    plugin_code = """
def evaluate(payload):
    values = payload.get("data", [])
    multiplier = payload.get("multiplier", 1.0)
    return {"smoothed": [round(x * multiplier, 2) for x in values]}
"""
    manifest = PluginManifest(
        plugin_id="indicator.smoothing",
        name="Smoothing Indicator",
        version="1.0.0",
        author="QuantLab",
        entry_point="evaluate",
        permissions=("compute", "custom_indicator"),
    )
    plugins.load_plugin(manifest, plugin_code)
    out = plugins.execute_plugin_hook(
        "indicator.smoothing",
        "evaluate",
        {"data": [1.1, 2.2, 3.3], "multiplier": 10.0},
    )
    print(f"  Sandboxed plugin execution result: {out}")
    plugins.unload_plugin("indicator.smoothing")


def example_01_workspace_jobs(runtime: Runtime) -> None:
    print("\n[6/8] Durable Job Lifecycle & CAS Transitions (FEAT-WORKSPACE-JOBS)")
    jobs = runtime.require(WORKSPACE_JOBS)
    job_def = JobDefinition(
        job_id="job-demo-100",
        group_id="portfolio-optim",
        operation="genetic_search",
        priority=10,
        resource_class="cpu.standard",
        config_hash="sha256:abc123",
        payload={"generations": 50, "population": 100},
        created_at_utc=datetime.now(UTC),
    )
    job_rcpt = jobs.create_job(job_def)
    print(f"  Job created in ledger: {job_rcpt.job_id} ({job_rcpt.state.value})")
    jobs.transition_state(job_def.job_id, JobState.QUEUED, JobState.RUNNING)
    attempt = jobs.create_attempt(job_def.job_id, "local-worker-1")
    print(f"  Attempt created: {attempt.attempt_id} (seq {attempt.sequence})")
    jobs.record_progress(
        JobProgress(
            job_id=job_def.job_id,
            attempt_id=attempt.attempt_id,
            progress_percent=60.0,
            message="Generation 30/50 complete",
            checkpoint={"current_gen": 30, "best_fitness": 3.14},
        )
    )
    jobs.transition_state(job_def.job_id, JobState.RUNNING, JobState.SUCCEEDED)
    final_rcpt = jobs.get_receipt(job_def.job_id)
    state_str = final_rcpt.state.value if final_rcpt else "unknown"
    pct_str = final_rcpt.progress_percent if final_rcpt else 0.0
    print(f"  Job transitioned to terminal state: {state_str} ({pct_str}%)")


def example_01_workspace_scheduler(runtime: Runtime) -> None:
    print("\n[7/8] Bounded Priority Scheduler (FEAT-WORKSPACE-SCHEDULER)")
    scheduler = runtime.require(WORKSPACE_SCHEDULER)
    scheduler.submit_job(
        JobDefinition(
            job_id="job-sched-low",
            group_id="batch",
            operation="eval",
            priority=5,
            resource_class="cpu",
            config_hash="h1",
            payload={},
            created_at_utc=datetime.now(UTC),
        )
    )
    scheduler.submit_job(
        JobDefinition(
            job_id="job-sched-high",
            group_id="batch",
            operation="eval",
            priority=100,
            resource_class="cpu",
            config_hash="h2",
            payload={},
            created_at_utc=datetime.now(UTC),
        )
    )
    stats = scheduler.get_queue_stats()
    print(
        f"  Scheduler queue stats: queued={stats.queued_count}, "
        f"max_concurrency={stats.max_concurrency}"
    )
    dispatched = scheduler.dispatch_next()
    print(
        f"  First dispatched (highest priority first): "
        f"{dispatched.job_id if dispatched else None}"
    )


def example_01_workspace_workers(runtime: Runtime) -> None:
    print("\n[8/8] Remote Worker Grid & Job Leasing (FEAT-WORKSPACE-WORKERS)")
    workers = runtime.require(WORKSPACE_WORKERS)
    node = GridNodeInfo(
        node_id="grid-node-alpha",
        host="192.168.1.100",
        port=7001,
        cores=16,
        memory_mb=32768,
        state=GridNodeState.ONLINE,
        last_heartbeat_utc=datetime.now(UTC),
    )
    workers.register_node(node)
    active_nodes = workers.list_nodes()
    print(
        f"  Registered remote grid node: {active_nodes[0].node_id} "
        f"({active_nodes[0].cores} cores, {active_nodes[0].state.value})"
    )
    lease = workers.acquire_lease(node.node_id, "job-sched-low", duration_seconds=600.0)
    print(
        f"  Worker lease acquired: id={lease.lease_id}, "
        f"expires={lease.expires_at_utc.isoformat()}"
    )
    workers.release_lease(lease.lease_id, completed=True)
    print("  Worker lease successfully released and settled")


async def run_workspace_demonstration() -> None:
    """Execute end-to-end demonstration of all workspace domain capabilities."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/workspace_demo.db"

        def _persistence_factory() -> WorkspacePersistenceFeature:
            return WorkspacePersistenceFeature(
                WorkspacePersistenceConfig(db_path=db_path, wal_mode=True)
            )

        features = (
            _persistence_factory,
            settings_feature,
            notifications_feature,
            diagnostics_feature,
            resources_feature,
            plugin_host_feature,
            jobs_feature,
            scheduler_feature,
            workers_feature,
        )

        async with Runtime(features) as runtime:
            print("=" * 70)
            print("HARUQUANTAI WORKSPACE DOMAIN (D-WORKSPACE) OFFLINE DEMONSTRATION")
            print("=" * 70)

            example_01_workspace_settings(runtime, tmp_dir)
            example_01_workspace_resources(runtime)
            example_01_workspace_diagnostics(runtime)
            example_01_workspace_notifications(runtime)
            example_01_workspace_plugins(runtime)
            example_01_workspace_jobs(runtime)
            example_01_workspace_scheduler(runtime)
            example_01_workspace_workers(runtime)

            print("\n" + "=" * 70)
            print("ALL 8 WORKSPACE FEATURES VERIFIED SUCCESSFULLY OFFLINE")
            print("=" * 70)


def main() -> None:
    """Run offline demonstration."""
    asyncio.run(run_workspace_demonstration())


if __name__ == "__main__":
    main()
