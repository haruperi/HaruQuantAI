"""WF-DATA-011: audit a reversible MT5 source-readiness transition."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_market_data_request,
    build_source_descriptor,
    build_source_license_policy,
    build_source_promotion_request,
    data_settings_context,
    get_market_data,
    get_source_descriptor,
    promote_source,
    register_source,
    run_data_migrations,
    unwrap_data_response,
)
from app.utils import create_auth_context, generate_id, utc_now

WORKFLOW_ID = "WF-DATA-011"
STAGES = (
    "Compose MT5 and read its current staging descriptor.",
    "Build authenticated normalization, quality, and sign-off evidence.",
    "Promote only with the descriptor's complete evidence package.",
    "Demote immediately and preserve audited reversibility.",
)

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)


def _market_request(data_kind, *, timeframe, limit):
    """Build one bounded genuine MT5 request inline."""
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
        timeframe=timeframe if data_kind == "bars" else None,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute authenticated promotion and demotion in temporary state."""
    print(f"{WORKFLOW_ID} — Source Readiness and Promotion")
    print("INPUT BOUNDARY — operator evidence package and AuthContext")

    with tempfile.TemporaryDirectory(prefix="wf-data-011-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///workflow.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            request_id = generate_id("req")
            run_data_migrations(request_id)

            genuine_resp = get_market_data(
                _market_request("bars", timeframe="M1", limit=1)
            )
            genuine = unwrap_data_response(
                genuine_resp, operation="get_market_data", request_id=request_id
            )

            # Stage 1 — Compose MT5 and read its current staging descriptor.
            _stage(1)
            candidate_id = "mt5-workflow-candidate"
            evidence = ("normalization", "quality", "operator_signoff")
            register_source(
                build_source_descriptor(
                    source_id=candidate_id,
                    readiness="staging",
                    capabilities=("ohlcv",),
                    requires_credentials=True,
                    requires_network=True,
                    supports_writes=False,
                    schema_version="v1",
                    timezone="UTC",
                    revision=genuine.source_metadata.get(
                        "source_revision", "mt5-observed"
                    ),
                    license_policy=build_source_license_policy(
                        source_id=candidate_id,
                        status="approved",
                        permitted_workflows=("research",),
                        export_allowed=False,
                        attribution_required=False,
                    ),
                    identity_mapping_revision="mt5-workflow-v1",
                    promotion_evidence=evidence,
                ),
                object,  # type: ignore[arg-type]
            )
            descriptor_resp = get_source_descriptor(candidate_id)
            descriptor = unwrap_data_response(
                descriptor_resp,
                operation="get_source_descriptor",
                request_id=request_id,
            )

            # Stage 2 — Build authenticated normalization, quality, and sign-off evidence.
            _stage(2)
            now = utc_now()
            auth = create_auth_context(
                contract_version="v1",
                schema_id="utils.auth_context.v1",
                principal_id="workflow-operator",
                principal_type="USER",
                roles=("admin",),
                permissions=(),
                scopes=(),
                tenant_or_environment="dev",
                request_id=request_id,
                workflow_id=generate_id("wf"),
                correlation_id=generate_id("cor"),
                issued_at=now,
            )
            assert descriptor.promotion_evidence == evidence

            # Stage 3 — Promote only with the descriptor's complete evidence package.
            _stage(3)
            promoted_resp = promote_source(
                build_source_promotion_request(
                    source_id=candidate_id,
                    target_readiness="production",
                    evidence=evidence,
                    request_id=request_id,
                ),
                auth,
                timestamp_ns=1,
            )
            promoted = unwrap_data_response(
                promoted_resp, operation="promote_source", request_id=request_id
            )

            # Stage 4 — Demote immediately and preserve audited reversibility.
            _stage(4)
            demoted_resp = promote_source(
                build_source_promotion_request(
                    source_id=candidate_id,
                    target_readiness="staging",
                    evidence=("operator_signoff",),
                    request_id=generate_id("req"),
                ),
                auth,
                timestamp_ns=2,
            )
            demoted = unwrap_data_response(
                demoted_resp, operation="promote_source", request_id=request_id
            )

            print(
                "Readiness transition:",
                descriptor.readiness,
                promoted.readiness,
                demoted.readiness,
            )
    print("OUTPUT BOUNDARY — audited reversible SourceDescriptor readiness")


if __name__ == "__main__":
    main()
