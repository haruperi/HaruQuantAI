"""Immutable observation-ledger evidence for FEAT-DATA-16."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.services.data import (
    build_data_settings,
    build_research_source_policy,
    build_verified_research_source,
    data_settings_context,
    get_research_source_value_field,
    normalize_research_provider_payload,
    persist_research_provider_records,
    persist_research_source_observations,
    persist_verified_research_source,
    project_research_source_observation,
    query_research_source_observations,
    run_data_migrations,
)
from app.utils import generate_id


def test_observation_revision_and_decision_time(tmp_path: Path) -> None:
    """Persist corrections immutably and filter by historical availability."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    settings = build_data_settings(
        database_url="sqlite:///data.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )
    with data_settings_context(settings):
        run_data_migrations(generate_id("req"))
        first = persist_research_source_observations(
            "doc-1",
            "bls",
            (
                {
                    "series_id": "CUUR0000SA0",
                    "observation_period": "2025-M06",
                    "value": "322.561",
                    "unit": "index",
                },
            ),
            published_at=now,
            available_at=now,
            retrieved_at=now,
            parser_version="bls-v2-v1",
            request_id=generate_id("req"),
        )[0]
        second = persist_research_source_observations(
            "doc-2",
            "bls",
            (
                {
                    "series_id": "CUUR0000SA0",
                    "observation_period": "2025-M06",
                    "value": "322.562",
                    "unit": "index",
                },
            ),
            published_at=now + timedelta(days=1),
            available_at=now + timedelta(days=1),
            retrieved_at=now + timedelta(days=1),
            parser_version="bls-v2-v1",
            request_id=generate_id("req"),
        )[0]
        historical = query_research_source_observations(
            now,
            source_id="bls",
            request_id=generate_id("req"),
        )

    assert get_research_source_value_field(first, "revision") == 1
    assert get_research_source_value_field(second, "revision") == 2
    assert get_research_source_value_field(second, "previous_observation_id") == (
        get_research_source_value_field(first, "observation_id")
    )
    assert len(historical) == 1
    assert project_research_source_observation(historical[0])["value"] == "322.561"


def test_normalized_provider_batch_persists_documents_and_values(
    tmp_path: Path,
) -> None:
    """Connect deterministic provider normalization to immutable persistence."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    payload = (
        Path(__file__).parents[1] / "fixtures" / "research_sources" / "treasury.json"
    ).read_bytes()
    records = normalize_research_provider_payload(
        "treasury-fiscal-data",
        payload,
        observed_at=now,
    )
    policy = build_research_source_policy(
        "treasury-v1",
        "treasury-fiscal-data",
        ("api.fiscaldata.treasury.gov",),
        ("dev",),
        ("research",),
        ("US",),
        False,
        30,
        5,
        1.0,
        None,
    )
    settings = build_data_settings(
        database_url="sqlite:///data.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )
    with data_settings_context(settings):
        run_data_migrations(generate_id("req"))
        documents = persist_research_provider_records(
            records,
            payload,
            source_id="treasury-fiscal-data",
            source_kind="macro",
            asset_scope=("USD",),
            issuer_scope=(),
            macro_series_scope=("debt-to-penny",),
            language="en",
            license_id="public-official-data",
            environment="dev",
            decision_use="research",
            policy=policy,
            retrieved_at=now,
            request_id=generate_id("req"),
        )
        observations = query_research_source_observations(
            now,
            source_id="treasury-fiscal-data",
            request_id=generate_id("req"),
        )

    assert len(documents) == 1
    assert len(observations) == 1
    assert get_research_source_value_field(documents[0], "document_kind") == (
        "fiscal_observations"
    )
    assert project_research_source_observation(observations[0])["unit"] == "USD"

    with data_settings_context(settings):
        manifest = build_verified_research_source(
            "treasury-fiscal-data",
            now,
            "debt-to-penny",
            "treasury-fiscal-data-v1",
            hashlib.sha256(payload).hexdigest(),
            ("dev", "research"),
            "public-official-data",
        )
        persisted_manifest = persist_verified_research_source(
            manifest,
            request_id=generate_id("req"),
        )
    assert (
        get_research_source_value_field(persisted_manifest, "external_record_id")
        == "debt-to-penny"
    )
